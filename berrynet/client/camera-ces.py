#!/usr/bin/python3

import argparse
import os
import time

from datetime import datetime

import cv2

from berrynet import logger
from berrynet.comm import Communicator
from berrynet.comm import payload


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        '--mode',
        default='stream',
        help='Camera creates frame(s) from stream or file. (default: stream)'
    )
    ap.add_argument(
        '--fps',
        type=int,
        default=1,
        help='Frame per second in streaming mode. (default: 1)'
    )
    ap.add_argument(
        '--filepath',
        default='',
        help='Input image path in file mode. (default: empty)'
    )
    ap.add_argument(
        '--dirpath',
        default='',
        help='Input image dir in file mode. (default: empty)'
    )
    ap.add_argument(
        '--broker-ip',
        default='localhost',
        help='MQTT broker IP.'
    )
    ap.add_argument(
        '--broker-port',
        default=1883,
        type=int,
        help='MQTT broker port.'
    )
    return vars(ap.parse_args())


def main():
    args = parse_args()

    comm_config = {
        'subscribe': {},
        'broker': {
            'address': args['broker_ip'],
            'port': args['broker_port']
        }
    }
    comm = Communicator(comm_config, debug=True)

    duration = lambda t: (datetime.now() - t).microseconds / 1000

    if args['mode'] == 'stream':
        counter = 0
        capture = cv2.VideoCapture(0)
        while True:
            status, im = capture.read()
            if (status is False):
                logger.warn('ERROR: Failure happened when reading frame')

            t = datetime.now()
            retval, jpg_bytes = cv2.imencode('.jpg', im)
            #mqtt_payload = payload.serialize_jpg(jpg_bytes)
            obj = {}
            obj['timestamp'] = datetime.now().isoformat()
            obj['bytes'] = payload.stringify_jpg(jpg_bytes)
            mqtt_payload = payload.serialize_payload([obj])
            comm.send('berrynet/data/rgbimage', mqtt_payload)
            logger.debug('send: {} ms'.format(duration(t)))

            time.sleep(1.0 / args['fps'])
    elif args['mode'] == 'file' and args['filepath'] != '':
        # Prepare MQTT payload
        im = cv2.imread(args['filepath'])
        retval, jpg_bytes = cv2.imencode('.jpg', im)

        t = datetime.now()
        #mqtt_payload = payload.serialize_jpg(jpg_bytes)
        obj = {}
        obj['timestamp'] = datetime.now().isoformat()
        obj['bytes'] = payload.stringify_jpg(jpg_bytes)
        obj['meta'] = {
            "roi": [
                {
                    "top": -1,
                    "right": -1,
                    "left": -1,
                    "overlap_threshold": 0,
                    "bottom": -1
                }
            ]
        }
        mqtt_payload = payload.serialize_payload([obj])
        logger.debug('payload: {} ms'.format(duration(t)))
        logger.debug('payload size: {}'.format(len(mqtt_payload)))

        # Client publishes payload
        t = datetime.now()
        comm.send('berrynet/data/rgbimage', mqtt_payload)
        logger.debug('mqtt.publish: {} ms'.format(duration(t)))
        logger.debug('publish at {}'.format(datetime.now().isoformat()))
    elif args['mode'] == 'file' and args['dirpath'] != '':
        for filename in sorted(os.listdir(args['dirpath'])):
            # Prepare MQTT payload
            im = cv2.imread(os.path.join(args['dirpath'], filename))
            retval, jpg_bytes = cv2.imencode('.jpg', im)

            t = datetime.now()
            #mqtt_payload = payload.serialize_jpg(jpg_bytes)
            obj = {}
            obj['timestamp'] = datetime.now().isoformat()
            obj['bytes'] = payload.stringify_jpg(jpg_bytes)
            obj['meta'] = {
                "roi": [
                    {
                        "top": -1,
                        "right": -1,
                        "left": -1,
                        "overlap_threshold": 0,
                        "bottom": -1
                    }
                ]
            }
            mqtt_payload = payload.serialize_payload([obj])
            logger.debug('payload: {} ms'.format(duration(t)))
            logger.debug('payload size: {}'.format(len(mqtt_payload)))

            # Client publishes payload
            t = datetime.now()
            comm.send('berrynet/data/rgbimage', mqtt_payload)
            logger.debug('mqtt.publish: {} ms'.format(duration(t)))
            logger.debug('publish at {}'.format(datetime.now().isoformat()))

            time.sleep(1.0 / args['fps'])
    else:
        logger.error('User assigned unknown mode {}'.format(args['mode']))


if __name__ == '__main__':
    main()
