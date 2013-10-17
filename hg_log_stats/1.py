#!/usr/bin/env python

import datetime, os, sys

from mercurial import ui, hg


# http://stackoverflow.com/a/1924593/41948
# http://mercurial.selenic.com/wiki/MercurialApi#Change_contexts

# http://selenic.com/pipermail/mercurial/2010-April/031021.html
# https://bitbucket.org/mg/hgchart/src

# parse hg internal revctx.date() tuple
get_date_str = lambda x:  datetime.datetime.fromtimestamp(x[0]).date().isoformat()
                #  '%s GMT%+d' -x[1]/3600


def get_repo_stats(p):
    " p as repo path "
    date_first    = None
    date_last     = None
    count_days    = 0
    count_commits = 0
    all_users     = set()
    all_files     = set()

    try:
        repo = hg.repository(ui.ui(), p)
    except:
        return ('',) * 7
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
    try:
        date_last = get_date_str(revctx.date())
    except:
        date_last = ''

    return p, date_first, date_last, count_days, count_commits, len(all_files), ', '.join(all_users)


if '__main__' == __name__:
    projects = os.listdir('.')
    result = map(get_repo_stats, projects)
    result.sort(key=lambda x:x[3], reverse=True)
    for r in result:
        print 'Project %s' % r[0]
        print '  From %s to %s, %s days active developing with %s commits to %s files.\n  Contributors: %s' % r[1:]