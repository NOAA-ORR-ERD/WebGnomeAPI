.. keywords
   horizontal diffusion, diffusion, mixing, horizontal, eddy diffusivity
   
Random spreading, i.e. diffusion, is included by a simple random walk with a square unit probability. 
The random walk is based on the **Diffusion Coefficient** which represents the horizontal 
eddy diffusivity in the water. The model default is 100,000 |cm2s|.

.. |cm2s| replace:: cm\ :sup:`2`\ s\ :sup:`-1`\

The **Uncertain Factor** only applies if the Uncertainty Solution option is 
selected in **Model Settings**. This factor will be randomly applied to the diffusion coefficient 
for the uncertainty particles.

The **Active Range** option can be used to limit the time interval in which the diffision is applied to the particles. The default is **Infinite** in which case the model will apply this diffusion at all times. A second option is to choose **Set Start/End Times**. In this case, the diffusion will be applied only while within the date range specified and will be inactive at other times. Multiple diffusion movers with varying coefficents can then be active at different times in the model simulation.

