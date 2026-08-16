# git-fr:可续传 `git fetch` 的探索记录

> 用 atproto 仓库做实验,目标是把 `git fetch origin main --depth=1` 在烂网下"下到一半就死、重试从头再来"的问题,变成"每次下一点、中断了接着下、最终必然成功"。

## TL;DR

- 常规 `git fetch` 一次只下一个 pack,包含所有缺失对象;连接一断整个 pack 作废,重试从零开始。
- 最终方案两阶段:
  1. `git fetch --filter=blob:none --depth=1` —— 只拉 commit+tree,包只有 **156KB**;
  2. 用 `rev-list --objects --missing=print` 算缺失集合,按 **500 个 blob 一批**回填;每轮重算缺失、只补缺的。
- 回填的唯一可靠原语不是 `git fetch origin <sha>`,而是 git 原生 lazy fetch 的形态:
  `git -c fetch.negotiationAlgorithm=noop fetch <remote> --no-tags --no-write-fetch-head --recurse-submodules=no --filter=blob:none --stdin`
- 产物:`fr.sh` 脚本(用法见文末)。

## 背景

`git fetch origin main --depth=1` 在慢速/抖动网络上反复失败。这个仓库当时留下了 3 个 3–4MB 的 `tmp_pack_*` 残留——每个都是"大包下到一半死掉"的实锤。事后看,仓库其实已经被一次成功的 fetch 补全了(0 缺失),失败的是更早的几次尝试。

问题本质:pack 是**单一、不可断点续传**的传输单元。服务器打包、客户端索引,要么全有,要么全无。

## 设计思路

既然一个大 pack 会死,那就不要一个大 pack:

1. **先只拉元数据**。`--filter=blob:none`(partial clone)让服务器只发 commit+tree。对 atproto main,这只有 156KB,任何烂网都扛得住。
2. **再按小批次拉 blob**。每个批次是独立请求,失败只损失一批。
3. **每轮重算缺失**。`git rev-list --objects --missing=print` 本地列出现缺对象,只重下缺失的——中断后重跑即续传,天然幂等。

## 踩过的坑(按时间顺序)

### 坑 1:"报错但送达"是假象,送达的是验证动作

`git fetch origin <blobsha>` 每次都会打印 `fatal: bad object <sha>` + `error: ... did not send all necessary objects`,但事后检查对象**确实存在**。一度以为"报错但送达,忽略退出码即可"。

**真相**:送达的从来不是 fetch,而是我用来验证的 `git cat-file -t` / `--batch-check`。在 promisor 配置开启时,cat-file 碰到缺失对象会**触发 lazy fetch**——每个对象一次独立的 SSH 请求(约 5.5s)。"5/5 送达""9c00449d 送达"全部是这个假象。

教训:**验证手段不能触发你正在测的机制**。`cat-file` 会拉数据,`rev-list --missing=print` 不会(纯本地)。

### 坑 2:普通 `git fetch origin <sha>` 从不送达

把验证换成 `rev-list` 后真相暴露:普通 fetch 拿到的 pack 是**薄包**(thin pack)——服务器按客户端声明的 haves 做 delta 压缩。我们声明的 haves 是 `refs/remotes/origin/main`(一个 commit),服务器据此**假定我们拥有整棵树的全部 blob**,于是把目标 blob 压成"相对另一个我们其实没有的 blob 的 delta"。`index-pack --fix-thin` 找不到 base → 整个包丢弃 → **什么都不送达**。

所以:promisor 配置开不开都不影响——只要 haves 声明了树,服务器就会薄包化,批量越大越容易撞上缺失 base,整批报废。

### 坑 3:git 原生 lazy fetch 的秘密形态

最终用 `GIT_TRACE=1 git cat-file blob <missing>` 抓到了 git 自己 lazy fetch 时实际执行的命令:

```
git -c fetch.negotiationAlgorithm=noop fetch origin --no-tags \
  --no-write-fetch-head --recurse-submodules=no --filter=blob:none --stdin
```

关键:
- **`fetch.negotiationAlgorithm=noop`** —— 不发 haves,服务器没法薄包化,只能发完整对象;
- **`--filter=blob:none`** —— 显式声明的 want 会绕过过滤器直接发送(partial clone 语义);
- **`--stdin`** —— want 列表从 stdin 读,天然支持批量。

照抄之后,20/20、500/500 全部送达,输出干净无噪音。

### 坑 4:`grep -q` + `pipefail` 误删配置

脚本的清理逻辑要在"仓库完整"时删掉 promisor 配置。当时的判断条件是:

```bash
! missing_shas | grep -q .
```

`grep -q` 匹配到第一行就退出并**关闭管道**,上游 `rev-list` 收到 SIGPIPE 死掉。在 `set -o pipefail` 下管道状态是右起第一个非零(141),`!` 取反后变成"真",于是清理逻辑**误判没有缺失对象,把 promisor 配置删了**——紧接着的批量 fetch 全部退化成普通 fetch,整轮零送达。

修复:用 `missing_shas | wc -l`(消费完整管道)代替 `grep -q`。

### 坑 5:部分仓库上重跑 phase 1 会死

回填到一半重跑脚本,phase 1(`git fetch --filter=blob:none --depth=1`,此时 ref 已存在)报:

```
fatal: missing blob object '<sha>'
error: remote did not send all necessary objects
```

GIT_TRACE 显示死在 `index-pack --fix-thin` 内部:它用 `rev-list --objects --exclude-promisor-objects` 校验薄包 delta base,**递归展开 base tree 到 blob 层**,而缺失 blob 不在任何 promisor pack 里(`--exclude-promisor-objects` 只排除在包里的)→ fatal。

而且注意:shallow 仓库的"up-to-date" fetch 并不真正免网络,它仍会协商、服务器仍会发包(所以才会走到 index-pack)。

修复:phase 1 失败但 ref 已存在时容忍并继续 phase 2(blob 照补,补完重跑一次 phase 1 就能推进 ref——此时树里所有 blob 都在,校验自然通过)。

### 坑 6:`--filter` 的 promisor 配置只在"真有传输"时自动写

`git fetch --filter=blob:none` 会在**实际传输了数据**时自动写 `remote.<name>.promisor=true` 和 `partialclonefilter`。如果仓库已是最新(ref 无新对象),fetch 不传输,**配置不会写**,phase 2 就悄悄退化成普通 fetch。必须在 phase 1 后**显式**设置这两项。

## 有意思的发现

- **`rev-list --objects --missing=print` 是零网络操作**。它在本地走 commit/tree,只按名字列出缺失对象,不读 blob 内容 → 不会触发 lazy fetch,可以用来放心地反复重算缺失集合。
- **`cat-file` 是 lazy fetch 触发器**。`cat-file -t`、`--batch-check`、`--batch` 在 promisor 仓库里访问缺失对象都会触发拉取(每个对象一次请求)。这既是坑 1 的根源,也意味着"让 git 自己干活"永远比你手搓协议稳。
- **"报错但送达"的错觉可以骗过几乎所有人**。`fatal: bad object` + `did not send all necessary objects` 组合出现时,对象可能确实在库里——但那是被后续验证动作拉来的。**只看退出码和对象存在性都不够,要看数据从哪来。**
- **失败 fetch 的 `tmp_pack_*` 残骸**:`git fetch` 被中断会留下 `tmp_pack_*` 文件,`git count-objects` 会标记为 garbage,但它们不会被自动清理,需要手动删。
- **三层 partial 状态**:`remote.<name>.promisor` + `remote.<name>.partialclonefilter`(操作层)、pack 旁边的 `.promisor` 标记文件(数据层)、`extensions.partialClone`(仓库格式层,仅 `git clone --filter` 会写)。补全后要全部清掉,仓库才真正回到"普通仓库"。
- **服务器端才是瓶颈**:500 个 blob 一批约 2.7 分钟,大头是 GitHub 逐 blob 的压缩耗时(单 blob 约 0.3s),不是网络。想快就得靠 `--max-fetches` 预算把工作切成可重复的多轮,而不是单轮拉大包。
- **haves 声明会反噬**:客户端声明的 haves 越多,服务器越敢做薄包 delta,而你仓库里实际缺失的 blob 就越可能成为"缺失 base"。**对 blob want,声明 haves 等于自断后路。**

## 验证结果

- 演示仓库:`git init` + `remote add`,3211 个缺失 blob 分 7 批全部补齐,`git fsck --connectivity-only` 干净,39 个包 repack 合并为 2 个,`.git` 11MB,重跑幂等。
- 真实仓库:跑通,ref 更新正常,零残留(配置、标记文件全部清掉),工作区未动。
- `--full` 模式:增量加深正常(201 → 401 commits 后按 `--max-fetches` 预算停下,重跑续传)。

## 用法

```bash
git fr                      # 默认 origin main:浅拉 + blob 回填
git fr origin main          # 同上
git fr --full               # 增量加深全史(--deepen=200/次)
git fr --full --max-fetches=3   # 每次跑 3 个请求,反复执行直到完成
git fr --batch=200          # 调批次大小
git fr --timeout=600        # 单请求卡死上限(秒)
```

安装:脚本命名为 `fr.sh` 放到 PATH(如 `~/.local/bin/git-fr`),`git fr` 即可用,无需 alias;或 `git config --global alias.fr '!<绝对路径>/fr.sh'`。

## 限制与注意事项

- 服务器需支持 partial clone:`uploadpack.allowFilter` + `uploadpack.allowReachableSHA1InWant`(GitHub、GitLab 均支持)。
- 回填中断后,**promisor 配置会被保留**(脚本只在仓库完整时才清理)——这是有意为之:续传依赖它。
- 每批 500 个 blob 约 2.5–3 分钟(服务器压缩耗时),全史场景按预算分多轮跑。
- 只做 fetch,不动工作区、不改已有 ref 之外的状态;本地分支不受影响。
