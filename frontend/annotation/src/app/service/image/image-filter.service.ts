import { Injectable } from '@angular/core';

@Injectable({
    providedIn: 'root'
})
export class ImageFilterService {

    constructor() { }

    sharpen(image) {
        return this.filterImage(this.convolute, image,
            [0, -1, 0,
                -1, 5, -1,
                0, -1, 0]
        );
    }

    getCanvas(w, h) {
        var c = document.createElement('canvas');
        c.width = w;
        c.height = h;
        return c;
    }

    getPixels(img) {
        var c = this.getCanvas(img.width, img.height);
        var ctx = c.getContext('2d');
        ctx.drawImage(img, 0, 0);
        return ctx.getImageData(0, 0, c.width, c.height);
    }

    filterImage(filter, image, var_args) {
        var args = [this.getPixels(image)];
        for (var i = 2; i < arguments.length; i++) {
            args.push(arguments[i]);
        }
        return filter.apply(this, args);
    }

    createImageData(w, h) {
        let canvas = document.createElement('canvas');
        let ctx = canvas.getContext('2d');
        return ctx.createImageData(w, h);
    }

    histogramEqualize(img) {
        let pixels = this.getPixels(img);
        let imageHsl = [];
        let imageLums = [];

        let data = pixels.data;
        for (let i = 0; i < data.length; i += 4) {
            let r = data[i];
            let g = data[i + 1];
            let b = data[i + 2];
            //var alpha = data[i+3];

            let hsl = this.rgbToHsl(r, g, b);
            imageHsl.push(hsl);
            imageLums.push(hsl[2]);
        }

        let lumLength = imageLums.length;

        // Compute histogram and histogram sum:
        let hist = new Array(101).fill(0);
        for (let i = 0; i < lumLength; i++) {
            hist[Math.floor(imageLums[i])]++;
        }

        for(let i=0; i < hist.length; i++) {
            hist[i] = hist[i] / lumLength;
        }

        // Compute integral histogram:
        let prev = hist[0];
        for (let i = 1; i < 101; i++) {
            hist[i] += prev;
            prev = hist[i];
        }

        // Equalize image:
        for (let i = 0; i < lumLength; ++i) {
            imageLums[i] = hist[Math.floor(imageLums[i])] * 100;
        }

        // update image data
        var output = this.createImageData(pixels.width, pixels.height);
        var dst = output.data;
        for (let i = 0; i < imageHsl.length; i++) {
            imageHsl[i][2] = imageLums[i];
            let rgb = this.hslToRgb(imageHsl[i][0], imageHsl[i][1], imageHsl[i][2]);

            let pixelI = i * 4;
            dst[pixelI] = rgb[0];
            dst[pixelI + 1] = rgb[1];
            dst[pixelI + 2] = rgb[2];
            dst[pixelI + 3] = data[pixelI + 3];
        }

        return output;
    }

    private hslToRgb(h, s, l) {
        // Must be fractions of 1
        s /= 100;
        l /= 100;

        let c = (1 - Math.abs(2 * l - 1)) * s,
            x = c * (1 - Math.abs((h / 60) % 2 - 1)),
            m = l - c / 2,
            r = 0,
            g = 0,
            b = 0;

        if (0 <= h && h < 60) {
            r = c; g = x; b = 0;
        } else if (60 <= h && h < 120) {
            r = x; g = c; b = 0;
        } else if (120 <= h && h < 180) {
            r = 0; g = c; b = x;
        } else if (180 <= h && h < 240) {
            r = 0; g = x; b = c;
        } else if (240 <= h && h < 300) {
            r = x; g = 0; b = c;
        } else if (300 <= h && h < 360) {
            r = c; g = 0; b = x;
        }
        r = Math.round((r + m) * 255);
        g = Math.round((g + m) * 255);
        b = Math.round((b + m) * 255);

        return [r, g, b];
    }

    private rgbToHsl(r, g, b) {
        // Make r, g, and b fractions of 1
        r /= 255;
        g /= 255;
        b /= 255;

        // Find greatest and smallest channel values
        let cmin = Math.min(r, g, b),
            cmax = Math.max(r, g, b),
            delta = cmax - cmin,
            h = 0,
            s = 0,
            l = 0;

        // Calculate hue
        // No difference
        if (delta == 0)
            h = 0;
        // Red is max
        else if (cmax == r)
            h = ((g - b) / delta) % 6;
        // Green is max
        else if (cmax == g)
            h = (b - r) / delta + 2;
        // Blue is max
        else
            h = (r - g) / delta + 4;

        h = Math.round(h * 60);

        // Make negative hues positive behind 360°
        if (h < 0)
            h += 360;

        // Calculate lightness
        l = (cmax + cmin) / 2;

        // Calculate saturation
        s = delta == 0 ? 0 : delta / (1 - Math.abs(2 * l - 1));

        // Multiply l and s by 100
        s = +(s * 100).toFixed(1);
        l = +(l * 100).toFixed(1);

        return [h, s, l];
    }

    convolute(pixels, weights, opaque) {
        var side = Math.round(Math.sqrt(weights.length));
        var halfSide = Math.floor(side / 2);
        var src = pixels.data;
        var sw = pixels.width;
        var sh = pixels.height;
        // pad output by the convolution matrix
        var w = sw;
        var h = sh;
        var output = this.createImageData(w, h);
        var dst = output.data;
        // go through the destination image pixels
        var alphaFac = opaque ? 1 : 0;
        for (var y = 0; y < h; y++) {
            for (var x = 0; x < w; x++) {
                var sy = y;
                var sx = x;
                var dstOff = (y * w + x) * 4;
                // calculate the weighed sum of the source image pixels that
                // fall under the convolution matrix
                var r = 0, g = 0, b = 0, a = 0;
                for (var cy = 0; cy < side; cy++) {
                    for (var cx = 0; cx < side; cx++) {
                        var scy = sy + cy - halfSide;
                        var scx = sx + cx - halfSide;
                        if (scy >= 0 && scy < sh && scx >= 0 && scx < sw) {
                            var srcOff = (scy * sw + scx) * 4;
                            var wt = weights[cy * side + cx];
                            r += src[srcOff] * wt;
                            g += src[srcOff + 1] * wt;
                            b += src[srcOff + 2] * wt;
                            a += src[srcOff + 3] * wt;
                        }
                    }
                }
                dst[dstOff] = r;
                dst[dstOff + 1] = g;
                dst[dstOff + 2] = b;
                dst[dstOff + 3] = a + alphaFac * (255 - a);
            }
        }
        return output;
    }
}
