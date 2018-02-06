import logging
import sys
from . import s3_ism_urls
from . import dash
from . import hls

__version__ = '0.0.1'

logging.basicConfig(
    level=log_level,
    format='%(levelname)s: %(asctime)s - %(funcName)s at %(lineno)d %(message)s'
)

logger = logging.getLogger(__name__)


class SegGen():
    """This main class provides easy to use methods to generate segments out of
    common formats.
    At this time this module provides an interface for HLS, Dash and Smooth.
    """

    def __init__(self, uso_endpoint_url, bucket_name, prefix='', **kwargs):
        """Initialization method.

        Arguments:
            uso_endpoint_url {strin} -- URL of USO
            bucket_name {string} -- Name of AWS S3 bucket to search for .ism files
            **kwargs {dict} -- Keyword Arguments that is supported
        """

        self.uso_endpoint_url = uso_endpoint_url
        self.bucket_name = bucket_name
        self.prefix = prefix
        self.aws_profile = None
        self.access_key_id = None
        self.secret_access_key = None

        if 'aws_profile' in kwargs:
            self.aws_profile = kwargs['aws_profile']

        if 'access_key_id' in kwargs:
            self.access_key_id = kwargs['access_key_id']

        if 'secret_access_key' in kwargs:
            self.secret_access_key = kwargs['secret_access_key']

        if 'count' in kwargs:
            self.count = kwargs['count']
        else:
            count = -1

    def _get_ism_path(self):
        """Gets ism paths for specified count.

        Returns:
            list -- List of ism keys.
        """


        s3_ism_obj = s3_ism_urls.IsmUrls(aws_profile=self.aws_profile, aws_access_key_id=self.access_key_id, aws_secret_access_key=self.secret_access_key)

        i = self.count
        ism_keys = list()
        for ism_key in s3_ism_obj.get_matching_s3_keys(bucket=self.bucket_name, prefix=self.prefix):
            if i == -1:
                ism_keys.append(ism_key)
            elif i == 0:
                break
            else:
                ism_keys.append(ism_key)
            i -= 1

        base_urls = s3_ism_obj.create_ism_url(self.uso_endpoint_url, ism_keys)

        return base_urls

    def _get_dash_segments(self, base_urls):
        """This private method generates DASH segments.

        Arguments:
            base_urls {string} -- Base URL to use for generating DASH segments

        Returns:
            list -- List of DASH segments
        """

        dash_client = dash.Dash()
        dash_segments = list()

        for base_url in base_urls:
            # Getting DASH/.mpd URLs
            dash_url = dash_client.get_callable_url(base_url)
            dash_mpd = dash_client.get_mpd_xml(dash_url)
            dash_segments.append(dash_client.get_mpd_segment_urls(base_url, dash_mpd))

        return dash_segments

    def _get_hls_segments(self, base_urls):
        """This private method generates HLS segments.

        Arguments:
            base_urls {string} -- Base URL to use for generating HLS segments

        Returns:
            list -- List of HLS segments
        """

        hls_client = hls.Hls()
        hls_segments = list()

        for base_url in base_urls:
            # Getting HLS/.m3u8 URLs
            hls_master_url = hls_client.get_master_url(base_url)
            hls_video_playlist = hls_client.get_video_playlist(hls_master_url)
            hls_segments.append(hls_client.get_segments(hls_video_playlist))

        return hls_segments

    def _get_smooth_segments(self, base_urls):
        """This private method generates Smooth segments.

        Arguments:
            base_urls {string} -- Base URL to use for generating Smooth segments

        Returns:
            list -- List of Smooth segments
        """
        smooth_client = smooth.Smooth()
        smooth_segments = list()

        for base_url in base_urls:
            # Getting Smooth/manifest URLs
            smooth_master_url = smooth_client.get_smooth_url(base_url)
            smooth_xml = smooth_client.get_smooth_xml(smooth_master_url)
            smooth_segments.append(smooth_client.get_smooth_segment_urls(base_url, smooth_xml))

        return smooth_segments

    def get_format_segment_urls(self, **kwargs):
        """Public method that generates segments dependent on what provides in kwargs.

        Arguments:
            **kwargs {dict} -- Dictionary that can contain hsl, dash, smooth.

        Returns:
            list -- List of segments of specified media in kwargs.
        """

        all_segments = list()
        base_urls = self._get_ism_path()

        if 'hls' in kwargs:
            hls_segments = self._get_hls_segments(base_urls)
            all_segments.extend([seg for segs in hls_segments for seg in segs])
        if 'dash' in kwargs:
            dash_segments = self._get_dash_segments(base_urls)
            all_segments.extend([seg for segs in dash_segments for seg in segs])
        if 'smooth' in kwargs:
            smooth_segments = self._get_smooth_segments(base_urls)
            all_segments.extend([seg for segs in smooth_segments for seg in segs])

        return all_segments
