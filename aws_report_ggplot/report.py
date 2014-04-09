import csv
import datetime


writer = csv.writer(open('report_out.csv', 'w'))


fmt1 = '%d/%m/%y %H:%M:%s'

with open('report.csv') as csvfile:
    reader = csv.reader(csvfile)
    
    # first row
    for i, row in enumerate(reader):
        # Service, Operation, UsageType, Resource, StartTime, EndTime, UsageValue
        try:
            usage_type = row[2]
            resource = row[3]
            time = row[4]
            if i>1:
                time = datetime.datetime.strptime(fmt1, time)
                time = time.date.isoformat()
            usage_value = row[6]
            writer.writerow([usage_type, resource, time, usage_value])
        except IndexError:
            print type(row), row

