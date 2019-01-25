#!/usr/bin/env python3
import miniupnpc
import boto3
import json

DEBUG = False

HOSTED_ZONE_ID = 'Z1L78WVXXW80LD'
HOME_DNS_A_NAME = 'home.deeje.io'
session = boto3.Session(profile_name='home')
client = session.client('route53')


def get_external_ip_address():
    u = miniupnpc.UPnP()
    u.discoverdelay = 200
    u.discover()
    u.selectigd()
    return u.externalipaddress()


def check_for_existing_record():
    response = client.test_dns_answer(
        HostedZoneId=HOSTED_ZONE_ID,
        RecordName=HOME_DNS_A_NAME,
        RecordType='A',
    )
    if DEBUG:
        print(json.dumps(response))

    return response


def assert_response_is_valid(response: dict):
    if response["ResponseMetadata"]["HTTPStatusCode"] is not 200:
        raise SystemExit("non 200 status when listing aws dns records")


def upsert_dns_record(external_ip_address: str):
    return client.change_resource_record_sets(
        HostedZoneId=HOSTED_ZONE_ID,
        ChangeBatch={
            'Changes': [
                {
                    'Action': 'UPSERT',
                    'ResourceRecordSet': {
                        'Name': HOME_DNS_A_NAME,
                        'Type': 'A',
                        'Region': 'us-west-2',
                        'TTL': 300,
                        'SetIdentifier': HOME_DNS_A_NAME,
                        'ResourceRecords': [
                            {
                                'Value': external_ip_address
                            },
                        ],
                    }
                },
            ]
        }
    )


if __name__ == "__main__":
    external_ip_address = get_external_ip_address()
    existing_record_response = check_for_existing_record()
    assert_response_is_valid(existing_record_response)

    if external_ip_address not in existing_record_response["RecordData"]:
        print('updating {} -> {}'.format(HOME_DNS_A_NAME, external_ip_address))
        print(upsert_dns_record(external_ip_address))

