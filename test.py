import logging
from CCPAdaptor import CCPAdaptor
from ZKBAdaptor import ZKBAdaptor
from Tracker import Tracker

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

ccp_adaptor = CCPAdaptor()
zkb_adaptor = ZKBAdaptor()

tracker = Tracker(None, ccp_adaptor, zkb_adaptor, 1282059165, 10000060, 8)

while True:
    tracker.run()