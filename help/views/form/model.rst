.. keywords
   start, duration, incident, setttings, uncertainty

Setup some basic information for your scenario.

* Choose a meaningful **Incident Name** or use the default.
* Set the **Start Time** for your incident by clicking on the calendar or entering it in the box. In general, this should be the same as the spill start time -- if the model start time is later than the spill start time this will cause an error. Also, dates pre-1970 are not supported.
* Specify the **Model Time Zone** for you incident. This will be used to compare with (and adjust) time dependent infomation loaded into the model.
* Set the model run **Duration**.
* Specify the **Time Step** length. For accurate numerics, the time step should be based on the resolution of the model inputs (currents/winds). For more on this see the |faq_link|.
* Choose whether to include **Uncertainty** in the particle transport. Note that at this time, this only affects the movement of the particles (not the weathering) Uncertainty particles will not weather (their mass will be conservative). |uncert_link|
* Choose to **Run backwards** from the Start time to examine where particles impacting a site may have come from.

.. |uncert_link| raw:: html

   <a href="/doc/uncertainty.html" target="_blank">Learn more about including uncertainty in the WebGNOME Users manual.</a>

.. |faq_link| raw:: html

   <a href="/doc/faq.html" target="_blank">WebGNOME Users manual FAQ</a>