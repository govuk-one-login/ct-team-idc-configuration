# © 2023 Amazon Web Services, Inc. or its affiliates. All Rights Reserved.
# This AWS Content is provided subject to the terms of the AWS Customer Agreement available at
# http: // aws.amazon.com/agreement or other written agreement between Customer and either
# Amazon Web Services, Inc. or Amazon Web Services EMEA SARL or both.
import json
import boto3
import os
from botocore.exceptions import ClientError
from operator import itemgetter

client = boto3.client('sso-admin')

ACCOUNT_ID = os.environ['ACCOUNT_ID']


def list_existing_sso_instances():
    client = boto3.client('sso-admin')
    try:
        response = client.list_instances()
        return response['Instances'][0]
    except ClientError as e:
        print(e.response['Error']['Message'])


sso_instance = list_existing_sso_instances()


def get_mgmt_account_id():
    org_client = boto3.client('organizations')
    try:
        response = org_client.describe_organization()
        return response['Organization']['MasterAccountId']
    except ClientError as e:
        print(e.response['Error']['Message'])


mgmt_account_id = get_mgmt_account_id()


def get_mgmt_ps():
    try:
        p = client.get_paginator('list_permission_sets_provisioned_to_account')
        paginator = p.paginate(
            InstanceArn=sso_instance['InstanceArn'],
            AccountId=mgmt_account_id,)
        all_permissions = []
        for page in paginator:
            all_permissions.extend(page["PermissionSets"])
        return all_permissions
    except ClientError as e:
        print(e.response['Error']['Message'])
        return []


def getPS(ps):
    try:
        response = client.describe_permission_set(
            InstanceArn=sso_instance['InstanceArn'],
            PermissionSetArn=ps
        )
        return {'Name': response['PermissionSet']['Name'], 'Arn': response['PermissionSet']['PermissionSetArn']}
    except ClientError as e:
        print(e.response['Error']['Message'])


def handler(event, context):
    permissions = []
    mgmt_ps = get_mgmt_ps()
    deployed_in_mgmt = True if ACCOUNT_ID == mgmt_account_id else False
    try:
        p = client.get_paginator('list_permission_sets')
        paginator = p.paginate(InstanceArn=sso_instance['InstanceArn'])

        for page in paginator:
            for permission in page['PermissionSets']:
                if not deployed_in_mgmt:
                    if permission not in mgmt_ps:
                        permissions.append(getPS(permission))
                else:
                    permissions.append(getPS(permission))
        return sorted(permissions, key=itemgetter('Name'))
    except ClientError as e:
        print(e.response['Error']['Message'])
