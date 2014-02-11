import pandas as pd
from ggplot import * 
import dateutil
a=pd.read_csv('1.csv')
print a.dtypes
#b=a[a['Resource']=='MY_BUCKET']
b=a[( a['Operation']=='GetObject')&(a['UsageValue']>=1e10 )]
b['Date'] = [dateutil.parser.parse(x) for x in b['StartTime']]
print b

ggplot(
	aes(x='Date', y='UsageValue', color='Resource' ), data=b
) + scale_x_date(breaks=date_breaks('1 month'), labels='%b %Y') + geom_point()