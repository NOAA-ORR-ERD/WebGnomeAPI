.. keywords
   continuous release, amount spilled, constant spill, emulsion, override, trajectory, map

The Point or Line Release form contains multiple sections where you may enter information. If you are running the model using the Oil Fate Wizard (weathering only mode) you will not see 
the sections titled **Position** nor **Windage**. These sections are only relevant to trajectory simulations.

**General Spill Properties**

* Enter the **Name** of the spill. Use descriptive names, particularly if you will be adding more than one spill.
* Enter the **Time of Release** or select the date and time using the calendar icon next to the entry box. To enter a date and time manually, use date format yyyy/mm/dd and time format 00:00 (24-hour clock). To select a date using the calendar, click on the calendar icon next to the start time entry. Click on the left or right arrows to change the month, and click on a date square to select it. Select a time from the list to the right of the calendar, scrolling up or down as necessary.
* The **Model Time Zone** can be changed if desired (by default it will match the time zone specified in the **Model Settings**). Changing it in this form will also apply the change to the model. 
* Enter the **Release Duration** and select units from the drop-down menu.
* Either enter the **Amount Released** (total spill amount) or **Release Rate** and select units from the drop-down menu. The other field will be dynamically calculated. Note that if **Release Duration** is set to zero, setting **Relase Rate** will be disabled.
* The **Number of Particles** defaults to 1000 but can be edited if desired (e.g. for a large volume spill).

**Substance/Oil Section**

* The default substance is "Non-weathering". In this case, particles will move under the influence of wind and currents but their properties will not change over time. To model weathering processes, you must first specify an oil. Oils can be downloaded from the ADIOS oil database using the link in the form. Oil information is stored in a JSON (text) file format. Once an oil file is loaded, summary information on the oil is displayed, along with an option to edit the Emulsification defaults for the oil.

* Note on **Emulsification Onset After**: The emulsification algorithm assumes that emulsion begins when some percentage of the oil has evaporated. You have the option of overriding the default value and specifying when you want emulsion to begin. Click on the button next to the entry field. Choose hours from the drop-down menu and type in the number of hours that have elapsed before emulsion begins, or choose percent from the drop-down menu and type in the percent of the spill that has evaporated.

**Position Section**

You can specify the spill position one of two ways.

* Select **Place on Map** to bring up an interactive map display.
* Enter latitude and longitude values using the text boxes.

**Windage Section**

These parameters change the amount of direct wind influence on the particles.