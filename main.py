from algorithms import *


def underwater_enhance(image, red_c=2.2, blue_c=3.2, apply_gray_world=True,
                       kernel_size=9, sharp_gamma_c=1.8, sharp_c=0.3, gamma_c=2.2):
    '''
    :param image           : image of dtype uint8
    :param red_c           : compensation for red channel
    :param blue_c          : compensation for blue channel
    :param apply_gray_world: apply Gray World algorithm after compensation
    :param kernel_size     : kernel size of Gaussian Blur when sharpening
    :param sharp_gamma_c   : gamma correction coefficient when sharpening
    :param sharp_c         : sharpen coefficient when sharpening
    :param gamma_c         : gamma correction coefficient when adjusting luminance
    :return                : image, wb_image,
                             gamma_image, sharpen_image, enhancement image
    '''

    # ------------
    #  Read Image
    # ------------
    image = uint2float(image)

    # -----------------
    #  White Balancing
    # -----------------

    wb_image = compensate_white_balancing(image,
                                          red_c, blue_c, apply_gray_world)

    # ---------------------------------
    #  Gamma Correction and Sharpening
    # ---------------------------------

    gamma_image, sharpen_image = gamma_and_sharpen(wb_image, kernel_size,
                                                   sharp_gamma_c, sharp_c,
                                                   gamma_c)

    # ---------------------
    #  Weights Calculation
    # ---------------------
    gamma_weights = weights(gamma_image)
    sharpen_weights = weights(sharpen_image)

    gamma_weight = sum(gamma_weights)
    sharpen_weight = sum(sharpen_weights)

    gamma_weight, sharpen_weight = normalize_weights(
        [gamma_weight, sharpen_weight]
    )

    # --------
    #  Fusion
    # --------

    reconstruct_image = fusion([gamma_image, sharpen_image],
                               [gamma_weight, sharpen_weight])
    images = [image, wb_image, gamma_image, sharpen_image, reconstruct_image]

    # titles = 'original white-balancing gamma sharpen recontruct'.split()
    # fig, axes = plt.subplots(len(images), 2, figsize=(5, 35))
    # for i, (title, img) in enumerate(zip(titles, images)):
    #     plot_image(img, axes[i, 0], title)
    #     plot_hist(img, axes[i, 1], title)
    # plt.show()
    return images

def main():
    pass

if __name__ == '__main__':
    main()
