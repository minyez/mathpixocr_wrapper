## Mathpix OCR wrapper

This repository includes a Python wrapper for Mathpix OCR API
and an Automator workflow to emulate the Mathpix Snip Tool.

### Requirements

Python 3. 3.5 or higher should be sufficient.

In order to grab image from the clipboard, the [pillow](https://pillow.readthedocs.io/en/stable/) package is used.
Optionally, you can directly parse the path of image by option `-i`.

### Usage

Prepare a JSON file named `.mathpix_api.json` in the same path as the Python script

```json
{
    "app_key": "xxxxxxxxxxxx",
    "app_id": "xxxxxxxxxxxx"
}
```

The values should be those from your Mathpix account. Then try the example

```shell
python3 mathpixocr.py -p --format latex_styled -i example.png
```

### Limits

The scripts is only tested on macOS. Meanwhile, when grabing image from the clipboard,
the image will be copied as '.temp_eq.png' under the same path as the script. Therefore you
have to put the script under the directory you have the writting permission.

### License

Public domain

