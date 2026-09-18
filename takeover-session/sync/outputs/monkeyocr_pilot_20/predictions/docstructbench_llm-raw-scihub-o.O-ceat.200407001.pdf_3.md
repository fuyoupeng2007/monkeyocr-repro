$$
\begin{array} { r l r } { \Lambda _ { \mathrm { r } } ( \mathbf { r } ) } & { { } = } & { \lambda _ { \mathrm { b e d } } ( \mathbf { r } ) + \mathbf { K } _ { 1 } \, \, \mathrm { P e } _ { 0 } \, \, \frac { \mathbf { u } _ { \mathrm { c } } } { \overline { { \mathbf { u } } } _ { 0 } } \, \, f ( \mathbf { R } - \mathbf { r } ) \, \lambda _ { \mathrm { f } } } \end{array}
$$  

The damping function f(R-r) remains the same as for the mass transfer (Eq.(11)), while the slope parameter and the damping parameter are slightly modified to, respectively,  

$$
\mathbf { K } _ { 1 } = \frac { 1 } { 8 }
$$  

$$
\mathrm { K _ { 2 } ~ = ~ 0 . 4 4 ~ + ~ 4 ~ e x p \! \left( - \frac { R e _ { 0 } } { 7 0 } \right) }
$$  

The heat release by adsorption, see [19] for $\Delta H_{\mathrm{ad}}$, is derived in the last term on the right-hand side of Eq.(14) from the change of solids load with time. This very term couples the energy with the mass balance, so that both have to be solved simultaneously in order to account for thermal effects. Heat transfer resistances to or in the particles are neglected. The terms $\delta_{\mathrm{bed}}(\mathbf{r})$ and $\lambda_{\mathrm{bed}}(\mathbf{r})$ in Eqs. (8), (10), (15) and (17) describe the isotropic effective diffusivity and thermal conductivity of the bed without fluid flow. Boundary and initial conditions for Eqs. (7) and (14) are recapitulated in Tab. 1.  

On the basis of the above described general model various reductions are possible by neglecting thermal effects, the radial coordinate or gas-to-particle and intraparticle mass transfer resistances. From such reduced versions the following has been considered in more detail in the present work:  

1) plug-flow model (1-D) with local equilibrium between the gas and the solids, 2) plug-flow model (1-D) with mass transfer resistance to the solids, 3) 2-D maldistribution model with local equilibrium, 4) 2-D maldistribution model with mass transfer resistance to the solids.  

In our terminology "plug flow" means that every influence of the radial coordinate is neglected, including the influence of the wall on porosity and flow velocity. However, axial dispersion, as expressed by the dispersion coefficient $D_{\mathrm{ax}}$, is accounted for, so that the equation  

$$
\bar { \psi } \frac { \partial \mathbf { Y } } { \partial \mathbf { t } } = \mathbf { D _ { a x } } \frac { \partial ^ { 2 } \mathbf { Y } } { \partial z ^ { 2 } } - \bar { \mathbf { u } } _ { 0 } \frac { \partial \mathbf { Y } } { \partial \mathbf { z } } - [ 1 - \bar { \psi } ] \frac { \partial \mathbf { X } \rho _ { \mathrm { p } } } { \partial \mathbf { t } } \frac { } { \rho _ { \mathrm { f } } }
$$  

applies to the isothermal plug flow models (models 1 and 2). Eq. (20) is the classical, conventional way to model packed bed adsorbers. Local equilibrium corresponds, in terms of the two-layers model from [19], to the limiting case of $\beta_{\mathrm{f}} \rightarrow \infty$ and $\beta_{\mathrm{p}} \rightarrow \infty$. At this limit, equilibrium is considered to be sufficient for calculating the response of the solid phase to changes of the concentration in the fluid. Model 4 is our complete, highest order model, as previously outlined and in exact correspondence to [13–18]. Mainly this model has been evaluated for both isothermal and non-isothermal conditions.  

# 4 Numerical Solution and its Validation  

The partial differential equation or equations of the various models have been solved by the method of lines. The numerical calculations were conducted for different mesh densities, and the results accepted when the change of calculated gas moisture content values was lower than 0.05 % of the maximal difference of gas moisture content appearing in the packed bed. When the error was bigger, the mesh was made denser. Since the width of the concentration front is, in many cases, not much smaller than the length of the bed, equidistant meshes have been used in the axial direction. In the maldistribution models (models 3 and 4 in the previous section) meshes that were denser near the wall than in the center of the tube have been applied.  

To check the numerical procedure, respective results have been compared with available analytical solutions. One of such a solution is attributed to Anzelius [1] and refers to model 2 after the classification of section 3, additionally reduced by neglecting axial dispersion ($\mathrm{D}_{\mathrm{ax}}=0$). Furthermore, it is assumed that the sorption equilibrium is throughout linear ("Henry's law"), and that the bed is long. The mass transfer resistance is attributed to the fluid phase. Then, axial profiles can be derived to  

$$
\frac { \mathrm { C } } { \mathrm { C _ { i n } } } \! = \! \frac { 1 } { 2 } \mathrm { e r f c } \Big ( \sqrt { \overline { { \xi } } } - \sqrt { \overline { { \tau } } } \Big )
$$  

with  

$$
\xi = 6 \frac { \beta _ { \mathrm { ~ f ~ } } } { \mathrm { ~ d ~ p ~ u ~ } } \frac { z } { \psi } \frac { 1 - \psi } { }
$$  

and  

$$
\tau = 6 \frac { \upbeta _ { \mathrm { f } } } { \mathrm { d _ { p } K } } \left( \mathrm { t } - \frac { z } { \mathrm { u } } \right)
$$  

In Eq. (21) the concentration of adsorbate in the gas phase, C, is used instead of the content, Y, assuming an ini  

Table 1. Boundary and initial conditions for models.   


<html>
<table><thead><tr><th rowspan="2">t&gt;0</th><th rowspan="2">0≤r≤R</th><th rowspan="2">z=0</th><th colspan="1" rowspan="2">$\begin{matrix} \mathbf{Y}=\mathbf{Y}_{\mathrm{in}}&\text{or}\\ \mathbf{u}_0(\mathbf{Y}_{\mathrm{in}}-\mathbf{Y})=-\mathbf{D_{ax}}\frac{\partial\mathbf{Y}}{\partial\mathbf{u}}& \end{matrix}$</th><th rowspan="2">T=T<sub>in</sub></th></tr><tr></tr><tr><th></th><th></th><th>z=L</th><th>$\begin{matrix} \frac{\partial \mathbf{X}}{\partial z}=0\\ \frac{\partial \mathbf{Y}}{\partial z}=0\\ \frac{\partial T}{\partial z}=0& \end{matrix}$</th><th></th></tr></thead><tbody><tr><td>t&gt;0</td><td>0≤z≤L</td><td>r=0</td><td>$\begin{matrix} \frac{\partial \mathbf{X}}{\partial r}=0\\ \frac{\partial \mathbf{Y}}{\partial r}=0\\ \frac{\partial T}{\partial r}=0& \end{matrix}$</td><td>$\frac{\partial T}{\partial r}$=0</td></tr><tr><td></td><td></td><td>r=R</td><td>$\begin{matrix} \frac{\partial \mathbf{X}}{\partial r}=0\\ \frac{\partial \mathbf{Y}}{\partial r}=0\\ \mathbf{T}=$T<sub>w</sub>& \end{matrix}$</td><td></td></tr><tr><td>t=0</td><td>0≤r≤R</td><td>0≤z≤L</td><td>$\begin{matrix} \mathbf{X}(\mathbf{r},z)&=\mathbf{X}_0\\ \mathbf{Y}(\mathbf{r},z)&=\mathbf{Y}_0\\ \mathbf{T}(\mathbf{r},z)&=\mathbf{T}_0& \end{matrix}$</td><td></td></tr></tbody></table>
</html>  