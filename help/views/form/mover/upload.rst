.. keywords
   currents, movers, roms, fvcom, cats, hyrodynamic model

**NetCDF format**

For currents and winds in NetCDF format, at present, only specific output formats are supported (eventually any CF-compliant file with the necessary variables should be compatible). Typical output from ocean models like ROMS or any UGRID/SGRID compliant format should be supported. 

NetCDF model output is typically output in Greenwich Mean Time (GMT). The option to **Adjust time in file** allows the data to be shifted to work in a different time zone (for example, if you want to input the spill time and other inputs using a local time zone). For time zones in the US, the shift in hours is:

* Hawaii Standard Time -10
* Alaska Standard/Daylight Time -9/-8
* Pacific Standard/Daylight Time -8/-7
* Mountain Standard/Daylight Time -7/-6
* Central Standard/Daylight Time -6/-5
* Eastern Standard/Daylight Time -5/-4

Note, these are all negative numbers as they are behind (or earlier than) the GMT time zone.

**CATS format**

This format is used solely by NOAA ERD. Contact the WebGNOME team if you require information on using this format.

**Deprecated ASCII formats**

These are still supported at present as a few model outputs are only available in these formats (for example, Texas Water Board Development models in GOODS). Its likely that support for these formats will be removed in the near future.

**More Information**
For more information on supported NetCDF or ASCII formats, see the |file_formats_link|.

.. |file_formats_link| raw:: html

   <a href="https://gnome.orr.noaa.gov/doc/pygnome/file_formats/index.html" target="_blank">GNOME supported file formats document</a>

.. |goods_link| raw:: html

   <a href="https://gnome.orr.noaa.gov/goods" target="_blank">the GNOME Data Server (GOODS)</a>
