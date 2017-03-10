from nose import SkipTest

from funtests import transport


class test_sqla(transport.TransportCase):
    transport = 'sqlalchemy'
    prefix = 'sqlalchemy'
    event_loop_max = 10
    connection_options = {'hostname': 'sqla+sqlite://'}

    def before_connect(self):
        try:
            import sqlalchemy  # noqa
        except ImportError:
            raise SkipTest('sqlalchemy not installed')
