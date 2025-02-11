import boto3
import requests
import time
import urllib.request
# Get instance metadata (to fetch its own instance ID)


def get_instance_id():
    try:
        instanceid = urllib.request.urlopen(
            'http://169.254.169.254/latest/meta-data/instance-id').read().decode()
        return instanceid
    except requests.RequestException as e:
        print(f"Error fetching instance metadata: {e}")
        return None


# AWS Clients
# Change to your region
ec2_client = boto3.client('ec2', region_name='eu-central-1')
instance_id = get_instance_id()

if not instance_id:
    print("Unable to retrieve instance ID. Exiting...")
    exit(1)


# Creates an AMI of the given instance.
def create_ami(instance_id):
    try:
        ami_name = f"Transcription-Server-AMI-{int(time.time())}"
        response = ec2_client.create_image(
            InstanceId=instance_id,
            Name=ami_name,
            NoReboot=True  # Avoids rebooting the instance
        )
        ami_id = response['ImageId']
        print(f"AMI Creation Started: {ami_id}")
        return ami_id
    except Exception as e:
        print(f"Error creating AMI: {e}")
        return None


# Waits until the AMI is available.
def wait_for_ami(ami_id):

    try:
        print(f"Waiting for AMI {ami_id} to become available...")
        waiter = ec2_client.get_waiter('image_available')
        waiter.wait(ImageIds=[ami_id])
        print(f"AMI {ami_id} is now available!")
        return True
    except Exception as e:
        print(f"Error waiting for AMI: {e}")
        return False


# Creates a launch template using the new AMI.
def create_launch_template(ami_id):
    try:
        launch_template_name = "Transcription-Server-Template"
        response = ec2_client.create_launch_template(
            LaunchTemplateName=launch_template_name,
            LaunchTemplateData={
                'ImageId': ami_id,
                'InstanceType': 'g4dn.xlarge',
                'KeyName': 'ssh_access',
                'SecurityGroupIds': ['sg-0b37fa617eabd748d'],
                'BlockDeviceMappings': [
                    {
                        'DeviceName': '/dev/sda1',  # Root volume
                        'Ebs': {
                            'VolumeSize': 45,
                            'VolumeType': 'gp3',
                            'Iops': 16000,  # 16K IOPS
                            'Throughput': 1000,  # 1000 MB/s
                            'DeleteOnTermination': True
                        }
                    }
                ]
            }
        )
        template_id = response['LaunchTemplate']['LaunchTemplateId']
        print(f"Launch Template Created: {template_id}")
        return template_id
    except Exception as e:
        print(f"Error creating launch template: {e}")
        return None


# Main function to create AMI and launch template.
def main():
    print(f"Instance ID: {instance_id}")

    # Step 1: Create an AMI
    ami_id = create_ami(instance_id)
    if not ami_id:
        return

    # Step 2: Wait for AMI to be ready
    if not wait_for_ami(ami_id):
        return

    # Step 3: Create a Launch Template
    template_id = create_launch_template(ami_id)
    if template_id:
        print(
            f"Successfully created Launch Template {template_id} with AMI {ami_id}")


if __name__ == "__main__":
    main()
