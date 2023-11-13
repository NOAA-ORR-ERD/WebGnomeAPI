.. keywords
   subset, model, goods, ofs

The form to the right of the map has options for selecting the download parameters for the model output including the time range, time zone,  and the bounding box for the region of interest. 

**Time options**

The available model output time range is shown at the top of the form in UTC. Any time interval within this range can be selected. The specified **Start Time** and **End Time** will be interpreted as UTC unless an alternate time zone is selected from the Time Zone pull down list. If an alternate time zone is specified, the model output will be automatically converted to that time zone.

Model output is available on a variety of time steps (hourly, 6-hourly, et). Therefore, the time series downloaded may not adhere strictly to the start and end times specified, however, if model output is available, both the start and end times should be encompassed in the time series.

**Bounding box**

The model domain (for non-global models) is displayed on the map. The bounding box of the region of interest can be specifed either by clicking and dragging a rectangle on the map (release mouse button to draw the rectangle) or specify latitude and longitude values in the form for **West**, **North**, **East**, and **South** boundaries. If a map has been added to the model, the bounding box of the map is selected by default.


**Additional options**

* To download only surface currents, check **Surface Only** . At present, this is always checked as the 3-D currents are not (yet) utilized in WebGNOME.

* To download a map matching the selected region (rectangle) and add it to the model, check **Include Map**. This will replace any existing map previously added.

* If the ocean model output includes surface winds, an option to **Include Winds** will be available. If checked, winds will be included in the download and a wind mover will be created simulanteously with the currents.




