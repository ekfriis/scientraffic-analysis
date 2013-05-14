# -*- coding: utf-8 -*-
"""
Tools to run random routes using the OSRM
"""

import itertools
import logging
import math
import numpy as np
import requests

log = logging.getLogger(__name__)


def generate_random_choices_forever(alist, mcfunc):
    """ Generate random choices from a list

    Don't stop.  Ever.

    :param: alist - a random access iterable to select from
    """
    while True:
        start_idx = np.random.randint(0, len(alist)-1)
        end_idx = np.random.randint(0, len(alist)-1)
        # protect against unlikely case
        if end_idx == start_idx:
            continue
        if not mcfunc or mcfunc(alist[start_idx], alist[end_idx]):
            yield (alist[start_idx], alist[end_idx])


def generate_random_choices(N, alist, mcfunc=None):
    """ Generate random choices from a list

    :param: N - number of choices to generate
    :param: alist - a random access iterable to select from

    """
    for i, output in enumerate(generate_random_choices_forever(alist, mcfunc)):
        if i >= N:
            break
        yield output


def generate_random_choices_exponential(N, alist):
    """ Generate random choices from a list

    The list will be distributed according to an exponentially
    falling distribution based on distances between the returned points.

    :param: N - number of choices to generate
    :param: alist - a random access iterable to select from

    """
    def distance(a, b):
        return np.hypot(*(a - b))
    pairs = itertools.izip(alist[:-1], alist[1:])
    max_distance = max(map(lambda x: distance(x[0], x[1]), pairs))

    def mc_selector(a, b):
        throw = np.random.random_sample()
        normalized_distance = distance(a, b) * 1./max_distance
        if throw < math.exp(-(normalized_distance**2)):
            return True
        return False

    for output in generate_random_choices(N, alist, mc_selector):
        yield output


def build_osrm_url(coords, host, port):
    """Build an OSRM query URL

    :param: coords - a two-tuple of integer (lat, lon) pairs.
        They should be scaled up by 1E5.
    :param: host - hostname of OSRM server
    :param: port - port of OSRM server
    """
    startpt, endpt = coords
    # we can't uses the requests params feature, since it
    # will escape the commas.
    url = 'http://{host}:{port}/viaroute?loc={loc1}'\
        '&loc={loc2}&instructions=false&raw=true'.format(
            host=host, port=port,
            loc1=','.join('%0.6f' % (x / 1E5) for x in startpt),
            loc2=','.join('%0.6f' % (x / 1E5) for x in endpt),
        )
    return url


def parse_osrm_output(response):
    """Parse the JSON object returned by OSRM

    Returns 4-D numpy array raw node steps, where the second
    axis has the form

    (node_id, duration, lat, lon)

    """
    return np.array(response.json()['raw_data'], dtype=int)


def run_route(coords, host='localhost', port=5000):  # pragma: nocover
    """Query an OSRM server for a route

    Returns the (decoded) JSON `output from OSRM`_.

    .. _output from OSRM: https://github.com/DennisOSRM/
        Project-OSRM/wiki/Output-json

    :param coords: 2-tuple of starting & ending (lat, lon)
    """
    log.info("Running route from %s => %s", coords[0], coords[1])
    url = build_osrm_url(coords, host, port)
    response = requests.get(url)
    if response.status_code != 200:
        log.error("Route lookup with %s failed with %i.",
                  url, response.status_code)
        return None
    return coords, url, parse_osrm_output(response)
