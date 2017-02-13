#!/bin/bash
sudo yum update
sudo yum install ruby
sudo yum install wget
cd /home/ec2-user
wget https://aws-codedeploy-{region_name}.s3.amazonaws.com/latest/install
chmod +x ./install
sudo ./install auto
