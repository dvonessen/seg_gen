import xmltodict
import requests
import logging
import sys

logging.basicConfig(
    level=log_level,
    format='%(levelname)s: %(asctime)s - %(funcName)s at %(lineno)d %(message)s'
)
logger = logging.getLogger(__name__)


class Smooth():
    """Class which is usefull to get Manifest XML files, dict representation of Manifest XML files
    and Smooth segment URLs.
    Segment URLs are usefull to use them in performance testing tools like locust.
    Example:

    from seg_gen import smooth
    base_url = 'http://www.example.com/path_to_video.ism/'
    smooth_client = Smooth()
    smooth_url = smooth_client.get_smooth_url(base_url)
    smooth_xml = smooth.get_smooth_xml(smooth_url)
    segment_url = smooth.get_smooth_segment_urls(base_url, smooth_xml)
    """

    def get_smooth_url(self, base_url):
        """""Builds URL to fetch manifest file

        Arguments:
            base_url {string} -- URL that points to ism file on USO

        Returns:
            string -- URL appended with /manifest
        """

        try:
            return base_url + 'manifest'
        except:
            logger.error('base_url must be type of string.')
            logger.debug('', exc_info=True)
            sys.exit(127)

    def get_smooth_xml(self, smooth_xml):
        """Returns dictionary with content of Manifest XML.

        Arguments:
            mpd_url {string} -- URL where to fetch Manifest XML. Mostly ends with /manifest.

        Returns:
            dictionary -- dict representation of Manifest XML.
        """

        try:
            response = requests.get(smooth_xml)
            if response.status_code == 200:
                return xmltodict.parse(response.content)
        except:
            logger.warning('Could not get manifest xml from manifest url.')
            logger.debug('', exc_info=True)
            return ''

    def get_smooth_segment_urls(self, base_url, smooth_xml):
        """Parses Manifest XML file to get all information to create segment URLs
        to call for performance testing.

        Arguments:
            base_url {string} -- URL that points to ism file on USO.
            smooth_xml {dict} -- Dict representation of Manifest XML file.

        Returns:
            list -- List of Segment URLS to use in performance testing tool.
        """

        try:
            stream_indexes = smooth_xml['SmoothStreamingMedia']['StreamIndex']

            for stream_index in stream_indexes:
                if 'video' in stream_index['@Type']:
                    stream_url_path = stream_index['@Url']
                    seg_time_lines = stream_index['c']
                    quality_level = stream_index['QualityLevel']['@Bitrate']

            segment_urls = list()
            duration = 0
            for seg_time_line in seg_time_lines:
                if '@t' in seg_time_line:
                    url = base_url + stream_url_path
                    url = url.replace('{bitrate}', quality_level)
                    url = url.replace('{start time}', seg_time_line['@t'])
                    segment_urls.append(url)
                    duration += int(seg_time_line['@d'])
                else:
                    url = base_url + stream_url_path
                    url = url.replace('{bitrate}', quality_level)
                    url = url.replace('{start time}', str(duration))
                    segment_urls.append(url)
                    duration += int(seg_time_line['@d'])
            return segment_urls
        except:
            logger.error('Could not generate smooth segments.')
            logger.debug('', exc_info=True)
            return []
