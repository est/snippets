#!/usr/bin/env python

import datetime, os, sys

from mercurial import ui, hg


# http://stackoverflow.com/a/1924593/41948
# http://mercurial.selenic.com/wiki/MercurialApi#Change_contexts

# http://selenic.com/pipermail/mercurial/2010-April/031021.html
# https://bitbucket.org/mg/hgchart/src

# parse hg internal revctx.date() tuple
get_date_str = lambda x:  datetime.datetime.fromtimestamp(x[0]).date()
                #  '%s GMT%+d' -x[1]/3600


def get_repo_stats(p):
    " p as repo path "
    date_first    = None
    date_last     = None
    totay_days    = 0
    count_days    = 0
    count_commits = 0
    all_users     = set()
    all_files     = set()

    try:
        repo = hg.repository(ui.ui(), p)

        date_prev = None
        revctx = None
        for rev in repo:
            revctx = repo[rev]

            date = revctx.date()

            if not date_first:
                date_first = get_date_str( date )

            count_commits += 1

            date_now = int(date[0]/3600/24)
            count_days += 1 if date_prev!=date_now else 0
            date_prev = date_now

            all_files |= set(revctx.files())
            all_users.add(revctx.user())

        date_last = get_date_str(revctx.date())
        total_days = (date_last - date_first).days
        return p, date_first.isoformat(), date_last.isoformat(), count_days, total_days, count_commits, len(all_files), all_users
    except:
        return ('',) * 8

if '__main__' == __name__:
    projects = os.listdir('.')
    result = map(get_repo_stats, projects)
    result.sort(key=lambda x:x[3], reverse=True)
    for r in result:
        print 'Project %s' % r[0]
        print '  %s - %s, %s/%s days, %s commits to %s files.' % r[1:-1]
        print '  %d contributors: %s' % (len(r[-1]), ', '.join(r[-1]))