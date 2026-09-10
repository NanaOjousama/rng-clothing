# Hood-Up Side Hair Visual Mask

Status: **STATIC PASS — FOCUSED LIVE RETEST REQUIRED**

## Strategy

The side-facing hairstyle remains fully enabled. The raised Hat already draws above Hair, so opaque hood fabric can visually cover selected hair pixels without cropping or replacing the hairstyle.

The right-side hood now:

- preserves the existing upper/front transparent opening;
- closes the lower opening in a four-step diagonal from logical rows 22–26;
- extends only the rear edge of the final shoulder/neck rows;
- keeps the face and upper/front hair visible;
- masks the lower/rear long-hair region with connected hood fabric.

Left is the exact mirrored construction. No face-side bulk, Hat anchor, scale, frame, draw order, or weather logic changed.

## Hair policy

`HideBackOnly` is the default again:

- hood up front/right/left: preserve full Hair;
- hood up back: hide Hair;
- hood down: preserve Hair everywhere.

`PreserveFrontOnly` remains available if a particular hairstyle projects beyond the new side silhouette.

## Versions

- Fashion Sense child: `1.5.0`
- Content Patcher child: `1.3.0`
- Static six-hoodie diagnostic pack: `1.8.0`

## Retest

- Right/left: upper/front hair remains visible.
- Right/left: lower long hair no longer protrudes through the hood/neck/shoulder area.
- Right/left: face remains unobstructed.
- Right/left: hood does not read excessively bulky.
- Back: Hair remains hidden under `HideBackOnly`.
- Front and hood-down directions remain unchanged.

