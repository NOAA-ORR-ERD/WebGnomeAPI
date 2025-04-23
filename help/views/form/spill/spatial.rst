.. keywords
   spill, NESDIS
   

**File Information (NESDIS Only)**

This section is automatically popluated based on the oil classification information in the uploaded shapefile. For example, NESDIS Marine Pollution Surveillance Reports typically have at most two classes: "potential oil" and "potential thicker oil". These are represented as "thin" and "thick" with specified defaults for **Thickness**. These should be reviewed and edited as appropriate. Alternatively, the total **Volume** per oil class can be specified. The **Area** of the oil class is used to transform between the two. This is calculated from the geometry of the shapes in the file and can not be edited. 

**Note**: This section will not be present if the checkbox designating a NOAA/NESDIS Marine Pollution Surveillance Report (MPSR) was not checked on file upload.

**General Spill Properties**

* Enter the **Name** of the spill. Use descriptive names, particularly if you will be adding more than one spill. By default this will be the name of the file.
* The **Release Time** is automatically set from the file if it can be parsed and correspods to the time of the imagery. The timezone in NESDIS pollution reports is UTC (current spill timezone is displayed for reference). To change the default, select the date and time using the calendar icon next to the entry box or enter a date and time manually. Use date format yyyy/mm/dd and time format 00:00 (24-hour clock). To select a date using the calendar, click on the calendar icon next to the start time entry. 
* Check **Adjust to Model Timezone** to convert the spill time to match the model timezone. 
* The **Model Time Zone** can be changed if desired (by default it will match the time zone specified in the **Model Settings**). Changing it in this form will also apply the change to the model. 
* Enter the **Release Duration** and select units from the drop-down menu. This option is not shown for NESDIS MPSRs.
* The total **Amount Released** is automatically calculated from the oil class volumes.
* The **Number of Particles** defaults to 1000 but can be edited if desired (e.g. for a large volume spill).

**Substance/Oil Section**

* The default substance is "Non-weathering". In this case, particles will move under the influence of wind and currents but their properties will not change over time. To model weathering processes, you must first specify an oil. Oils can be downloaded from the ADIOS oil database using the link in the form. Oil information is stored in a JSON (text) file format. Once an oil file is loaded, summary information on the oil is displayed, along with an option to edit the Emulsification defaults for the oil.

* Note on **Emulsification Onset After**: The emulsification algorithm assumes that emulsion begins when some percentage of the oil has evaporated. You have the option of overriding the default value and specifying when you want emulsion to begin. Click on the button next to the entry field. Choose hours from the drop-down menu and type in the number of hours that have elapsed before emulsion begins, or choose percent from the drop-down menu and type in the percent of the spill that has evaporated.

**Windage Section**

These parameters change the amount of direct wind influence on the particles.