import boto3
import logging
import sys

logging.basicConfig(
    level=log_level,
    format='%(levelname)s: %(asctime)s - %(funcName)s at %(lineno)d %(message)s'
)
logger = logging.getLogger(__name__)


class IsmUrls():
    """Lists Keys from S3-Bucket
    """

    def __init__(self, aws_profile=None, aws_access_key_id=None, aws_secret_access_key=None):
        """Init method

        Keyword Arguments:
            aws_profile {string} -- Profilename in AWS config/credentials file (default: {None})
            aws_access_key_id {string} -- AWS AccessKeyId which is used to authenticate
                                          against AWS S3 (default: {None})
            aws_secret_access_key {string} -- AWS SecretAccessKeyId used together
                                              with AWS AccessKeyId (default: {None})
        """

        self.aws_profile = aws_profile
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key

    def __get_matching_s3_objects(self, bucket, obj_prefix=''):
        """Helper method to generate a list of AWS S3 Key in Bucket with specified prefix

        Arguments:
            bucket {string} -- AWS S3 Bucketname
            obj_prefix {string} -- Object prefix to use for searching in S3 bucket

        Yields:
            string -- AWS S3 bucket key path
        """

        if self.aws_profile or (self.aws_access_key_id and self.aws_secret_access_key):
            session = boto3.Session(
                profile_name=self.aws_profile,
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key
                )

            s3 = session.client('s3')
        else:
            s3 = boto3.client('s3')

        kwargs = {'Bucket': bucket}

        if isinstance(obj_prefix, str):
            kwargs['Prefix'] = obj_prefix

        while True:
            response = s3.list_objects_v2(**kwargs)

            try:
                contents = response['Contents']
            except KeyError:
                logger.error('S3 Response does not contain Contents.')
                logger.debug('', exc_info=True)
                sys.exit(127)

            for obj in contents:
                key = obj['Key']
                if key.startswith(obj_prefix) and key.endswith('.ism'):
                    yield obj

            try:
                kwargs['ContinuationToken'] = response['NextContinuationToken']
            except KeyError:
                break

    def get_matching_s3_keys(self, bucket, prefix=''):
        """Searchs for Keys in S3 buckets

        Arguments:
            bucket {string} -- Name of AWS S3 bucket
            prefix {string} -- Key prefix to distinguish keys in S3 bucket

        Yields:
            string -- AWS S3 bucket key of .ism-files
        """

        for obj in self.__get_matching_s3_objects(bucket, prefix):
            yield obj['Key']

    def create_ism_url(self, base_url, ism_path):
        """Method that creates URL-Path to ism files

        Arguments:
            base_url {string} -- Base URL that is used to generate ism URLs
            ism_path {string} -- URL path where the ism is located,
                                 usually used in conjunction with
                                 get_matching_s3_keys definition
        Returns:
            string -- Callable ISM URLs
        """

        try:
            ism_url = list()
            for path in ism_path:
                ism_url.append(base_url+path+'/')
            return ism_url
        except:
            logger.error('No ISM files found"')
            logger.debug('', exc_info=True)
            sys.exit(127)
