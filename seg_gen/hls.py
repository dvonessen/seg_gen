import m3u8
import logging
import sys

logging.basicConfig(
    level=logging.ERROR,
    format='%(levelname)s: %(asctime)s - %(funcName)s at %(lineno)d %(message)s'
)
logger = logging.getLogger(__name__)


class Hls():
    """Class that provides methods to get information
    to performance testing HLS/m3u8 VOD streams

    from seg_gen import hls
    base_url = 'http://www.example.com/path_to_video.ism/'
    hsl_client = Hls()
    mpd_url = hsl_client.get_callable_url(base_url)
    mpd_xml = hsl_client.get_mpd_xml(mpd_url)
    mpd_segment_urls = hsl_client.get_mpd_segment_urls(base_url, mpd_xml)
    """

    def get_master_url(self, base_url):
        """""Builds URL to fetch .m3u8 file

        Arguments:
            base_url {string} -- URL that points to ism file on USO

        Returns:
            string -- URL appended with /.m3u8
        """

        try:
            return base_url + '.m3u8'
        except:
            logger.error('base_url must be type of string')
            logger.debug('', exc_info=True)
            sys.exit(127)

    def get_video_playlist(self, master_url):
        """Returns playlist with video and audio content

        Arguments:
            master_url {string} -- URL where to fetch the playlists. Mostly ends with /.m3u8.

        Returns:
            playlist object -- Video playlist object used to fetch segment URIs
        """
        try:
            m3u8_obj = m3u8.load(master_url)
            if m3u8_obj.is_variant:
                for playlist in m3u8_obj.playlists:
                    if 'video' in playlist.uri and playlist.stream_info.resolution is not None:
                        return playlist
        except:
            logger.warning('Could not get video playlist out of m3u8 URL.')
            logger.debug('', exc_info=True)
            return ''

    def get_segments(self, sub_playlist):
        """Returns all segment URIs used to load test USO server with.

        Arguments:
            sub_playlist {playlist object} -- Playlist object with segment URIs in.

        Returns:
            list -- List of segment URIs
        """
        try:
            loaded_sub_playlist = m3u8.load(sub_playlist.absolute_uri)
            segment_uris = list()
            for segment in loaded_sub_playlist.segments:
                segment_uris.append(segment.absolute_uri)
            return segment_uris
        except:
            logger.warning('Could not generate segments, maybe playlist generation failed.')
            logger.debug('', exc_info=True)
            return []
