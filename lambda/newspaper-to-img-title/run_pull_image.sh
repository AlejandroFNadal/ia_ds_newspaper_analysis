# sh script that runs serverless invoke -f pull_image -p {
   # "id": "cdc73f9d-aea9-11e3-9d5a-835b769c0d9c",
   # "detail-type": "Scheduled Event",
   # "source": "aws.events",
   # "account": "123456789012",
   # "time": ",
   # "region": "us-east-1",
   # "resources": [
   #   "arn:aws:events:us-east-1:123456789012:rule/ExampleRule"
   # ],
   # "detail": {}
#}
# time is changed on every execution, starting from 1970-01-01T00:00:00Z to 1970-02-01T00:00:00Z    


#!/bin/bash

d_start='2010-07-01'
end='2010-07-30'

start=$(date -d $d_start +%Y%m%d)
end=$(date -d $end +%Y%m%d)
while [[ $start -le $end ]]
do
        # command date is d_start concatenated with T
        command_date="${d_start}T00:00:00Z"
        echo "$command_date"
        # call command
        serverless invoke -f pull_image --data "{
                \"id\": \"cdc73f9d-aea9-11e3-9d5a-835b769c0d9c\",
                \"detail-type\": \"Scheduled Event\",
                \"source\": \"aws.events\",
                \"account\": \"123456789012\",
                \"time\": \"$command_date\",
                \"region\": \"us-east-1\",
                \"resources\": [
                        \"arn:aws:events:us-east-1:123456789012:rule/ExampleRule\"
                ]
        }"
        start=$(date -d"$start + 1 day" +"%Y%m%d")
        d_start=$(date -d"$d_start + 1 day" +"%Y-%m-%d")
        # sleep for 1 minute
        sleep 60
done
