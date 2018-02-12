import xmltodict
import requests
import logging
import sys

logging.basicConfig(
    level=logging.ERROR,
    format='%(levelname)s: %(asctime)s - %(funcName)s at %(lineno)d %(message)s'
)
logger = logging.getLogger(__name__)


class Dash():
    """Class which is usefull to get MPD XML files, dict representation of MPD XML files
    and MPD segment URLs.
    Segment URLs are usefull to use them in performance testing tools like locust.
    Example:

    from seg_gen import Mpd
    base_url = 'http://www.example.com/path_to_video.ism/'
    dash = Dash()
    mpd_url = dash.get_callable_url(base_url)
    mpd_xml = dash.get_mpd_xml(mpd_url)
    segment_url = dash.get_mpd_segment_urls(base_url, mpd_xml)
    """

    def __build_mpd_segment_url(self, base_url, extension_url, segment_url, repr_id, seq_time=None):
        """This helper method creates the mpd segment URLs.

        Arguments:
            base_url {string} -- URL where to get the .mpd file.
            extension_url {string} -- contains path of dash segments.
            segment_url {string} -- Template URL to generate the segment URL.
            repr_id {string} -- ID which represents the DASH video file.

        Keyword Arguments:
            seq_time {string} -- Wich segment URL you want to get (default: {None})

        Returns:
            string -- DASH segment URL
        """

        if not seq_time:
            segment_url = segment_url.replace('$RepresentationID$', str(repr_id))
        else:
            tmp_url = segment_url.replace('$RepresentationID$', str(repr_id))
            segment_url = tmp_url.replace('$Time$', str(seq_time))
        return base_url + extension_url + segment_url

    def get_callable_url(self, base_url):
        """Builds URL to fetch .mpd files

        Arguments:
            base_url {string} -- URL that points to ism file on USO

        Returns:
            string -- URL appended with /.mpd
        """

        try:
            return base_url + '.mpd'
        except:
            logger.error('base_url must be type of string')
            logger.debug('', exc_info=True)
            sys.exit(127)

    def get_mpd_xml(self, mpd_url):
        """Returns dictionary with content of MPD XML.

        Arguments:
            mpd_url {string} -- URL where to fetch MPD XML. Mostly ends with /.mpd.

        Returns:
            dictionary -- dict representation of MPD XML.
        """

        try:
            response = requests.get(mpd_url)
            if response.status_code == 200:
                return xmltodict.parse(response.content)
        except:
            logger.warning('Could not get mpd xml from mpd url.')
            logger.debug('', exc_info=True)
            return ''

    def get_mpd_segment_urls(self, base_url, mpd_xml):
        """Parses MPD XML file to get all information to create segment URLs
        to call for performance testing.

        Arguments:
            base_url {string} -- URL that points to ism file on USO.
            mpd_xml {dict} -- Dict representation of MPD XML file.

        Returns:
            list -- List of Segment URLS to use in performance testing tool.
        """

        try:
            extension_url = mpd_xml['MPD']['Period']['BaseURL']
            adaptation_sets = mpd_xml['MPD']['Period']['AdaptationSet']
            segment_urls = list()

            for adaptation_set in adaptation_sets:
                if 'video' in adaptation_set['@contentType']:
                    initial_url = adaptation_set['SegmentTemplate']['@initialization']
                    media_url = adaptation_set['SegmentTemplate']['@media']
                    seg_time_lines = adaptation_set['SegmentTemplate']['SegmentTimeline']['S']
                    video_id = adaptation_set['Representation']['@id']

            segment_urls.append(
                self.__build_mpd_segment_url(base_url, extension_url, initial_url, video_id))

            next_step = 0
            for seg_time_line in seg_time_lines[:-1]:
                if '@t' in seg_time_line:
                    segment_urls.append(
                        self.__build_mpd_segment_url(
                            base_url, extension_url, media_url, video_id, seg_time_line['@t']
                            )
                        )
                if '@r' in seg_time_line:
                    for repetition in range(int(seg_time_line['@r'])+1):
                        next_step = next_step + int(seg_time_line['@d'])
                        segment_urls.append(self.__build_mpd_segment_url(
                                base_url, extension_url, media_url, video_id, next_step))
                else:
                    next_step = next_step + int(seg_time_line['@d'])
                    segment_urls.append(self.__build_mpd_segment_url(
                                base_url, extension_url, media_url, video_id, next_step))
            return segment_urls
        except:
            logger.warning('Could not generate dash segments.')
            logger.debug('', exc_info=True)
            return []
