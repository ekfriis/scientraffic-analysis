# -*- coding: utf-8 -*-

import numpy
from nose.tools import eq_

from stanalysis.routerunner import generate_random_choices, build_osrm_url,\
    parse_osrm_output


def test_generate_random_choice():
    numpy.random.seed(0xDEADBEEF)
    eq_(list(generate_random_choices(5, range(10))),
        [(8, 1), (2, 1), (5, 1), (7, 4), (4, 0)])


def test_build_osrm_url():
    eq_(build_osrm_url(((34E5, -118E5), (35E5, -118E5)), 'the_host', 9999),
        'http://the_host:9999/viaroute?loc=34.000000,-118.000000&'
        'loc=35.000000,-118.000000&instructions=false&raw=true')


def test_parse_osrm_output():

    class MockResponse():
        def json(self):
            return {
                'raw_data': [
                    [0, 1, 2, 3],
                    [4, 5, 6, 7]
                ]
            }

    result = parse_osrm_output(MockResponse())
    assert(numpy.array_equal(
        result, numpy.array([[0, 1, 2, 3], [4, 5, 6, 7]], dtype=int)))
