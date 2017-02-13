#!/bin/bash
#!/bin/bash
sudo yum update
sudo pip install -G --upgrade pip
sudo pip install boto3
python /var/test_script/run_test.py
