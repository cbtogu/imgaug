from __future__ import print_function, division, absolute_import

import sys
# unittest only added in 3.4 self.subTest()
if sys.version_info[0] < 3 or sys.version_info[1] < 4:
    import unittest2 as unittest
else:
    import unittest
# unittest.mock is not available in 2.7 (though unittest2 might contain it?)
try:
    import unittest.mock as mock
except ImportError:
    import mock

import matplotlib
matplotlib.use('Agg')  # fix execution of tests involving matplotlib on travis
import numpy as np

from imgaug import augmenters as iaa
from imgaug import parameters as iap
from imgaug.testutils import reseed


class _TestPoolingAugmentersBase(object):
    def setUp(self):
        reseed()

    @property
    def augmenter(self):
        raise NotImplementedError()

    def _test_augment_keypoints__kernel_size_is_noop(self, kernel_size):
        from imgaug.augmentables.kps import Keypoint, KeypointsOnImage
        kps = [Keypoint(x=1.5, y=5.5), Keypoint(x=5.5, y=1.5)]
        kpsoi = KeypointsOnImage(kps, shape=(6, 6, 3))

        aug = self.augmenter(kernel_size)

        kpsoi_aug = aug.augment_keypoints(kpsoi)

        assert kpsoi_aug.shape == (6, 6, 3)
        assert np.allclose(kpsoi_aug.to_xy_array(),
                           [[1.5, 5.5],
                            [5.5, 1.5]])

    def test_augment_keypoints__kernel_size_is_zero(self):
        self._test_augment_keypoints__kernel_size_is_noop(0)

    def test_augment_keypoints__kernel_size_is_one(self):
        self._test_augment_keypoints__kernel_size_is_noop(1)

    def test_augment_keypoints__kernel_size_is_two__keep_size(self):
        from imgaug.augmentables.kps import Keypoint, KeypointsOnImage
        kps = [Keypoint(x=1.5, y=5.5), Keypoint(x=5.5, y=1.5)]
        kpsoi = KeypointsOnImage(kps, shape=(6, 6, 3))
        aug = self.augmenter(2, keep_size=True)

        kpsoi_aug = aug.augment_keypoints(kpsoi)

        assert kpsoi_aug.shape == (6, 6, 3)
        assert np.allclose(kpsoi_aug.to_xy_array(),
                           [[1.5, 5.5],
                            [5.5, 1.5]])

    def test_augment_keypoints__kernel_size_is_two__no_keep_size(self):
        from imgaug.augmentables.kps import Keypoint, KeypointsOnImage
        kps = [Keypoint(x=1.5, y=5.5), Keypoint(x=5.5, y=1.5)]
        kpsoi = KeypointsOnImage(kps, shape=(6, 6, 3))
        aug = self.augmenter(2, keep_size=False)

        kpsoi_aug = aug.augment_keypoints(kpsoi)

        assert kpsoi_aug.shape == (3, 3, 3)
        assert np.allclose(kpsoi_aug.to_xy_array(),
                           [[1.5/2, 5.5/2],
                            [5.5/2, 1.5/2]])

    def test_augment_keypoints__kernel_size_differs(self):
        from imgaug.augmentables.kps import Keypoint, KeypointsOnImage
        kps = [Keypoint(x=1.5, y=5.5), Keypoint(x=5.5, y=1.5)]
        kpsoi = KeypointsOnImage(kps, shape=(6, 6, 3))
        aug = self.augmenter(
            (iap.Deterministic(3), iap.Deterministic(2)),
            keep_size=False)

        kpsoi_aug = aug.augment_keypoints(kpsoi)

        assert kpsoi_aug.shape == (2, 3, 3)
        assert np.allclose(kpsoi_aug.to_xy_array(),
                           [[(1.5/6)*3, (5.5/6)*2],
                            [(5.5/6)*3, (1.5/6)*2]])

    def test_augment_keypoints__kernel_size_differs__requires_padding(self):
        from imgaug.augmentables.kps import Keypoint, KeypointsOnImage
        kps = [Keypoint(x=1.5, y=5.5), Keypoint(x=5.5, y=1.5)]
        kpsoi = KeypointsOnImage(kps, shape=(5, 6, 3))
        aug = self.augmenter(
            (iap.Deterministic(3), iap.Deterministic(2)),
            keep_size=False)

        kpsoi_aug = aug.augment_keypoints(kpsoi)

        assert kpsoi_aug.shape == (2, 3, 3)
        assert np.allclose(kpsoi_aug.to_xy_array(),
                           [[(1.5/6)*3, (5.5/5)*2],
                            [(5.5/6)*3, (1.5/5)*2]])

    def test_augment_polygons__kernel_size_differs(self):
        from imgaug.augmentables.polys import Polygon, PolygonsOnImage
        polys = [Polygon([(1.5, 5.5), (5.5, 1.5), (5.5, 5.5)])]
        psoi = PolygonsOnImage(polys, shape=(6, 6, 3))
        aug = self.augmenter(
            (iap.Deterministic(3), iap.Deterministic(2)),
            keep_size=False)

        psoi_aug = aug.augment_polygons(psoi)

        assert psoi_aug.shape == (2, 3, 3)
        assert np.allclose(psoi_aug.polygons[0].exterior,
                           [[(1.5/6)*3, (5.5/6)*2],
                            [(5.5/6)*3, (1.5/6)*2],
                            [(5.5/6)*3, (5.5/6)*2]])


# TODO add test that checks the padding behaviour
class TestAveragePooling(_TestPoolingAugmentersBase, unittest.TestCase):
    @property
    def augmenter(self):
        return iaa.AveragePooling

    def test___init___default_settings(self):
        aug = iaa.AveragePooling(2)
        assert len(aug.kernel_size) == 2
        assert isinstance(aug.kernel_size[0], iap.Deterministic)
        assert aug.kernel_size[0].value == 2
        assert aug.kernel_size[1] is None
        assert aug.keep_size is True

    def test___init___custom_settings(self):
        aug = iaa.AveragePooling(((2, 4), (5, 6)), keep_size=False)
        assert len(aug.kernel_size) == 2
        assert isinstance(aug.kernel_size[0], iap.DiscreteUniform)
        assert isinstance(aug.kernel_size[1], iap.DiscreteUniform)
        assert aug.kernel_size[0].a.value == 2
        assert aug.kernel_size[0].b.value == 4
        assert aug.kernel_size[1].a.value == 5
        assert aug.kernel_size[1].b.value == 6
        assert aug.keep_size is False

    def test_augment_images__kernel_size_is_zero(self):
        aug = iaa.AveragePooling(0)
        image = np.arange(6*6*3).astype(np.uint8).reshape((6, 6, 3))
        assert np.array_equal(aug.augment_image(image), image)

    def test_augment_images__kernel_size_is_one(self):
        aug = iaa.AveragePooling(1)
        image = np.arange(6*6*3).astype(np.uint8).reshape((6, 6, 3))
        assert np.array_equal(aug.augment_image(image), image)

    def test_augment_images__kernel_size_is_two__array_of_100s(self):
        aug = iaa.AveragePooling(2, keep_size=False)
        image = np.full((6, 6, 3), 100, dtype=np.uint8)
        image_aug = aug.augment_image(image)
        diff = np.abs(image_aug.astype(np.int32) - 100)
        assert image_aug.dtype.name == "uint8"
        assert image_aug.shape == (3, 3, 3)
        assert np.all(diff <= 1)

    def test_augment_images__kernel_size_is_two__custom_array(self):
        aug = iaa.AveragePooling(2, keep_size=False)

        image = np.uint8([
            [50-2, 50-1, 120-4, 120+4],
            [50+1, 50+2, 120+1, 120-1]
        ])
        image = np.tile(image[:, :, np.newaxis], (1, 1, 3))

        expected = np.uint8([
            [50, 120]
        ])
        expected = np.tile(expected[:, :, np.newaxis], (1, 1, 3))

        image_aug = aug.augment_image(image)
        diff = np.abs(image_aug.astype(np.int32) - expected)
        assert image_aug.dtype.name == "uint8"
        assert image_aug.shape == (1, 2, 3)
        assert np.all(diff <= 1)

    def test_augment_images__kernel_size_is_two__four_channels(self):
        aug = iaa.AveragePooling(2, keep_size=False)

        image = np.uint8([
            [50-2, 50-1, 120-4, 120+4],
            [50+1, 50+2, 120+1, 120-1]
        ])
        image = np.tile(image[:, :, np.newaxis], (1, 1, 4))

        expected = np.uint8([
            [50, 120]
        ])
        expected = np.tile(expected[:, :, np.newaxis], (1, 1, 4))

        image_aug = aug.augment_image(image)
        diff = np.abs(image_aug.astype(np.int32) - expected)
        assert image_aug.dtype.name == "uint8"
        assert image_aug.shape == (1, 2, 4)
        assert np.all(diff <= 1)

    def test_augment_images__kernel_size_differs(self):
        aug = iaa.AveragePooling(
            (iap.Deterministic(3), iap.Deterministic(2)),
            keep_size=False)

        image = np.uint8([
            [50-2, 50-1, 120-4, 120+4],
            [50+1, 50+2, 120+2, 120-1],
            [50-5, 50+5, 120-2, 120+1],
        ])
        image = np.tile(image[:, :, np.newaxis], (1, 1, 3))

        expected = np.uint8([
            [50, 120]
        ])
        expected = np.tile(expected[:, :, np.newaxis], (1, 1, 3))

        image_aug = aug.augment_image(image)
        diff = np.abs(image_aug.astype(np.int32) - expected)
        assert image_aug.dtype.name == "uint8"
        assert image_aug.shape == (1, 2, 3)
        assert np.all(diff <= 1)

    def test_augment_images__kernel_size_differs__requires_padding(self):
        aug = iaa.AveragePooling(
            (iap.Deterministic(3), iap.Deterministic(1)),
            keep_size=False)

        image = np.uint8([
            [50-2, 50-1, 120-4, 120+4],
            [50+1, 50+2, 120+2, 120-1]
        ])
        image = np.tile(image[:, :, np.newaxis], (1, 1, 3))

        expected = np.uint8([
            [(50-2 + 50+1 + 50-2)/3,
             (50-1 + 50+2 + 50-1)/3,
             (120-4 + 120+2 + 120-4)/3,
             (120+4 + 120-1 + 120+4)/3]
        ])
        expected = np.tile(expected[:, :, np.newaxis], (1, 1, 3))

        image_aug = aug.augment_image(image)

        diff = np.abs(image_aug.astype(np.int32) - expected)
        assert image_aug.dtype.name == "uint8"
        assert image_aug.shape == (1, 4, 3)
        assert np.all(diff <= 1)

    def test_augment_images__kernel_size_is_two__keep_size(self):
        aug = iaa.AveragePooling(2, keep_size=True)

        image = np.uint8([
            [50-2, 50-1, 120-4, 120+4],
            [50+1, 50+2, 120+1, 120-1]
        ])
        image = np.tile(image[:, :, np.newaxis], (1, 1, 3))

        expected = np.uint8([
            [50, 50, 120, 120],
            [50, 50, 120, 120]
        ])
        expected = np.tile(expected[:, :, np.newaxis], (1, 1, 3))

        image_aug = aug.augment_image(image)

        diff = np.abs(image_aug.astype(np.int32) - expected)
        assert image_aug.dtype.name == "uint8"
        assert image_aug.shape == (2, 4, 3)
        assert np.all(diff <= 1)

    def test_augment_images__kernel_size_is_two__single_channel(self):
        aug = iaa.AveragePooling(2, keep_size=False)

        image = np.uint8([
            [50-2, 50-1, 120-4, 120+4],
            [50+1, 50+2, 120+1, 120-1]
        ])
        image = image[:, :, np.newaxis]

        expected = np.uint8([
            [50, 120]
        ])
        expected = expected[:, :, np.newaxis]

        image_aug = aug.augment_image(image)

        diff = np.abs(image_aug.astype(np.int32) - expected)
        assert image_aug.dtype.name == "uint8"
        assert image_aug.shape == (1, 2, 1)
        assert np.all(diff <= 1)

    def test_get_parameters(self):
        aug = iaa.AveragePooling(2)
        params = aug.get_parameters()
        assert len(params) == 2
        assert len(params[0]) == 2
        assert isinstance(params[0][0], iap.Deterministic)
        assert params[0][0].value == 2
        assert params[0][1] is None


# TODO add test that checks the padding behaviour
# We don't have many tests here, because MaxPooling and AveragePooling derive
# from the same base class, i.e. they share most of the methods, which are then
# tested via TestAveragePooling.
class TestMaxPooling(_TestPoolingAugmentersBase, unittest.TestCase):
    @property
    def augmenter(self):
        return iaa.MaxPooling

    def test_augment_images(self):
        aug = iaa.MaxPooling(2, keep_size=False)

        image = np.uint8([
            [50-2, 50-1, 120-4, 120+4],
            [50+1, 50+2, 120+1, 120-1]
        ])
        image = np.tile(image[:, :, np.newaxis], (1, 1, 3))

        expected = np.uint8([
            [50+2, 120+4]
        ])
        expected = np.tile(expected[:, :, np.newaxis], (1, 1, 3))

        image_aug = aug.augment_image(image)
        diff = np.abs(image_aug.astype(np.int32) - expected)
        assert image_aug.shape == (1, 2, 3)
        assert np.all(diff <= 1)

    def test_augment_images__different_channels(self):
        aug = iaa.MaxPooling((iap.Deterministic(1), iap.Deterministic(4)),
                             keep_size=False)

        c1 = np.arange(start=1, stop=8+1).reshape((1, 8, 1))
        c2 = (100 + np.arange(start=1, stop=8+1)).reshape((1, 8, 1))
        image = np.dstack([c1, c2]).astype(np.uint8)

        c1_expected = np.uint8([4, 8]).reshape((1, 2, 1))
        c2_expected = np.uint8([100+4, 100+8]).reshape((1, 2, 1))
        image_expected = np.dstack([c1_expected, c2_expected])

        image_aug = aug.augment_image(image)
        diff = np.abs(image_aug.astype(np.int32) - image_expected)
        assert image_aug.shape == (1, 2, 2)
        assert np.all(diff <= 1)


# TODO add test that checks the padding behaviour
# We don't have many tests here, because MinPooling and AveragePooling derive
# from the same base class, i.e. they share most of the methods, which are then
# tested via TestAveragePooling.
class TestMinPooling(_TestPoolingAugmentersBase, unittest.TestCase):
    @property
    def augmenter(self):
        return iaa.MinPooling

    def test_augment_images(self):
        aug = iaa.MinPooling(2, keep_size=False)

        image = np.uint8([
            [50-2, 50-1, 120-4, 120+4],
            [50+1, 50+2, 120+1, 120-1]
        ])
        image = np.tile(image[:, :, np.newaxis], (1, 1, 3))

        expected = np.uint8([
            [50-2, 120-4]
        ])
        expected = np.tile(expected[:, :, np.newaxis], (1, 1, 3))

        image_aug = aug.augment_image(image)
        diff = np.abs(image_aug.astype(np.int32) - expected)
        assert image_aug.shape == (1, 2, 3)
        assert np.all(diff <= 1)

    def test_augment_images__different_channels(self):
        aug = iaa.MinPooling((iap.Deterministic(1), iap.Deterministic(4)),
                             keep_size=False)

        c1 = np.arange(start=1, stop=8+1).reshape((1, 8, 1))
        c2 = (100 + np.arange(start=1, stop=8+1)).reshape((1, 8, 1))
        image = np.dstack([c1, c2]).astype(np.uint8)

        c1_expected = np.uint8([1, 5]).reshape((1, 2, 1))
        c2_expected = np.uint8([100+1, 100+4]).reshape((1, 2, 1))
        image_expected = np.dstack([c1_expected, c2_expected])

        image_aug = aug.augment_image(image)
        diff = np.abs(image_aug.astype(np.int32) - image_expected)
        assert image_aug.shape == (1, 2, 2)
        assert np.all(diff <= 1)


# TODO add test that checks the padding behaviour
# We don't have many tests here, because MedianPooling and AveragePooling
# derive from the same base class, i.e. they share most of the methods, which
# are then tested via TestAveragePooling.
class TestMedianPool(_TestPoolingAugmentersBase, unittest.TestCase):
    @property
    def augmenter(self):
        return iaa.MedianPooling

    def test_augment_images(self):
        aug = iaa.MedianPooling(3, keep_size=False)

        image = np.uint8([
            [50-9, 50-8, 50-7, 120-5, 120-5, 120-5],
            [50-5, 50+0, 50+3, 120-3, 120+0, 120+1],
            [50+8, 50+9, 50+9, 120+2, 120+3, 120+4]
        ])
        image = np.tile(image[:, :, np.newaxis], (1, 1, 3))

        expected = np.uint8([
            [50, 120]
        ])
        expected = np.tile(expected[:, :, np.newaxis], (1, 1, 3))

        image_aug = aug.augment_image(image)
        diff = np.abs(image_aug.astype(np.int32) - expected)
        assert image_aug.shape == (1, 2, 3)
        assert np.all(diff <= 1)

    def test_augment_images__different_channels(self):
        aug = iaa.MinPooling((iap.Deterministic(1), iap.Deterministic(3)),
                             keep_size=False)

        c1 = np.arange(start=1, stop=9+1).reshape((1, 9, 1))
        c2 = (100 + np.arange(start=1, stop=9+1)).reshape((1, 9, 1))
        image = np.dstack([c1, c2]).astype(np.uint8)

        c1_expected = np.uint8([2, 5, 8]).reshape((1, 3, 1))
        c2_expected = np.uint8([100+2, 100+5, 100+8]).reshape((1, 3, 1))
        image_expected = np.dstack([c1_expected, c2_expected])

        image_aug = aug.augment_image(image)
        diff = np.abs(image_aug.astype(np.int32) - image_expected)
        assert image_aug.shape == (1, 3, 2)
        assert np.all(diff <= 1)
