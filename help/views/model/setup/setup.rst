.. keywords
   incident, weathering, trajectory, requested prediction, setup, calendar, configure

Setup View
^^^^^^^^^^

.. raw:: html

    Use Setup View to configure and edit a scenario to model. Individual panels are used to interact with different
    types of model input. Individual panels include buttons to add (<span class="glyphicon glyphicon-plus"></span>), 
    edit (<span class="glyphicon glyphicon-pencil"></span>), and delete (<span class="glyphicon glyphicon-trash"></span>) 
    components.<p>

Panels may contain multiple objects that can be edited individually. For example, multiple currents or winds can be added to the 
model and turned on/off as desired. Objects added in each panel will appear in a list at the bottom of the panel. 

Although its possible to set up the model in various ways, a typical simulation will include:

* A Map
* A Spill
* A Wind (either Point or Gridded)
* A Current
* Horizontal Diffusion

If an oil is specified as the substance that is spilled, information in the Water panel will also need to be specified as the weathering of 
the oil will depend on some water properties.

**Note on using multiple Winds**

In Setup View multiple winds can be added to the model. The weathering algorithms will always use the first wind in the list. There is no way to reorder the list, and turning off the wind will not prioritize the next wind in the list. In order to connect the weathering to a new wind, the old wind must be deleted.

**Advanced Settings**

When adding or editing a model object, a pull down list of Advanced Settings appears at the bottom of the form. Although
typically modified parameters appear within the form, additional control over model parameters can be accessed via this list. Note, 
that it is VERY possible to change parameters through this list in such a way that the model will not be able to run (very little 
validation is done on parameters that are entered this way). 

**Add Oil Removal Options**

These panels are optional and allow users to add various removal options like skimming, burning, and chemically dispersing oil. See the 
|location_link| for more information on the different options available.

**Simulation Timeline**

This timeline shows the model duration and the time range for all the objects added to it. This is particularly useful for making sure 
all your data is compatible (in time) and troubleshooting errors that result from incompatibilities. 

Special cases like a Constant Wind or Horizontal Diffusion are extrapolated for all time so they are shown extending across the entire timeline.

.. |location_link| raw:: html

   <a href="https://gnome.orr.noaa.gov/doc/" target="_blank">User Guide</a>