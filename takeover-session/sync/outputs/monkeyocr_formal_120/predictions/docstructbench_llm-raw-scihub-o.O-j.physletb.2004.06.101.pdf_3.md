For consistency, the time derivative of the constraints of (10) must vanish and hence they must have vanishing Poisson bracket with $H$. Using the fundamental Poisson brackets  

$$
\left[ U ( x ) , \pi ^ { U } ( y ) \right] = \delta ( x - y ) ,
$$  

etc., we find that the primary constraints of (10) imply the secondary constraints  

$$
( \Sigma , \, \Sigma _ { i } ) = \Big ( - \partial _ { k } \Pi _ { k } ^ { V } \, , \, \varepsilon ^ { i j k } \partial _ { j } \big ( \Pi _ { k } ^ { B } - m \mathrm { V } _ { k } \big ) - \mu ^ { 2 } B _ { i } \Big ) .
$$  

If $\mu^{2}=0$ (the Cremmer-Scherk model Lagrangian [1]), the constraints of (14) would become reducible as then $\partial_{i}\Sigma_{i}=0$ and only the transverse portions of $\Sigma_{i}$ are constraints. Furthermore, with $\mu^{2}\neq0$, the requirement $\dot{\Sigma}_{i}=0$ leads to a tertiary constraint  

$$
T _ { k } \equiv \mu ^ { 2 } \Pi _ { k } ^ { B } = 0
$$  

with $\Sigma_{i}$ and $T_{k}$ constituting second class constraints as  

$$
\left[ T _ { k } ( x ) , \, \Sigma _ { i } ( y ) \right] = \mu ^ { 4 } \delta _ { i k } \delta ( x - y ) .
$$  

All other constraints are first class and no further constraints need to be imposed for consistency. There are consequently five first class constraints ($\Phi^{U}$, $\Phi_{k}^{A}$ and $\Sigma$) and six second class constraints ($\Sigma_{i}$ and $T_{k}$). The constraints $\Phi^{U}$ and $\Sigma$ correspond to the usual gauge transformations $\delta W_{0}=\partial_{0}\Omega$, $\delta W_{i}=\partial_{i}\Omega$ associated with a gauge field $W_{\mu}$, while $\Phi_{k}^{A}$ is associated with the fact that in (12) $A_{k}$ acts merely as a Lagrange multiplier (i.e., it is not dynamical) and hence its value is completely arbitrary. Suitable gauge conditions associated with the first class constraints are  

$$
\left( \gamma ^ { U } , \gamma _ { k } ^ { A } , \gamma ^ { V } \right) = ( U , A _ { k } , \partial _ { k } V _ { k } ) = 0 .
$$  

From (10), (14), (15) and (17) it is evident that the only dynamical degrees of freedom are  

$$
V _ { i } ^ { T } \equiv \left( \delta _ { i j } - \partial _ { i } \partial _ { j } / \partial ^ { 2 } \right) V _ { j } .
$$  

We can verify this directly by explicitly eliminating the non-physical degrees of freedom in (4). First, one decomposes $V_{k}$, $A_{k}$ and $B_{k}$ into transverse ($T$) and longitudinal ($L$) parts where  

$$
\nabla \times { \bf V } ^ { L } \equiv 0 \equiv \nabla \cdot { \bf V } ^ { T } ,
$$  

etc., (4) now becomes  

$$
\begin{array} { r } { 2 L = ( \dot { \mathbf { B } } ^ { L } ) ^ { 2 } - \left( \nabla \cdot \mathbf { B } ^ { L } \right) ^ { 2 } + \left[ \dot { \mathbf { B } } ^ { T } - \nabla \times \mathbf { A } ^ { T } \right] ^ { 2 } + ( \dot { \mathbf { V } } ^ { T } ) ^ { 2 } - \left( \nabla \times \mathbf { V } ^ { T } \right) ^ { 2 } + \left[ \dot { \mathbf { V } } ^ { L } - \nabla U \right] ^ { 2 } } \\ { + 2 m \left[ \dot { \mathbf { V } } ^ { T } \cdot \left( \nabla \times \mathbf { A } ^ { T } \right) + \mathbf { B } ^ { L } \cdot \dot { \mathbf { V } } ^ { L } + \mathbf { B } ^ { T } \cdot \dot { \mathbf { V } } ^ { T } - \mathbf { B } ^ { L } \cdot \nabla U \right] + 2 \mu ^ { 2 } \left[ \mathbf { A } ^ { T } \cdot \mathbf { B } ^ { T } + \mathbf { A } ^ { L } \cdot \mathbf { B } ^ { L } \right] . } \end{array}
$$  

The equations of motion for $\mathbf{A}^{L}$ and $U$, respectively, imply that  

$$
\mathbf { B } ^ { L } \! = \! 0 \! = \! \dot { \mathbf { V } } ^ { L } - \nabla U ,
$$  

reducing $(20)$ to  

$$
2 L = \left( { \dot { \mathbf { V } } } ^ { T } \right) ^ { 2 } - \left( \nabla \times \mathbf { V } ^ { T } \right) ^ { 2 } + \left[ { \dot { \mathbf { B } } } ^ { T } - \nabla \times \mathbf { A } ^ { T } \right] ^ { 2 } + 2 m \mathbf { V } ^ { T } \cdot \left( \nabla \times \mathbf { A } ^ { T } \right) + 2 m \mathbf { B } ^ { T } \cdot { \dot { \mathbf { V } } } ^ { T } + 2 \mu ^ { 2 } \mathbf { A } ^ { T } \cdot \mathbf { B } ^ { T } .
$$  

Since  

$$
\mathbf { A } ^ { T } \cdot \mathbf { B } ^ { T } = - \left( \nabla \times \mathbf { A } ^ { T } \right) \cdot \left( \nabla ^ { 2 } \right) ^ { - 1 } \left( \nabla \times \mathbf { B } ^ { T } \right) ,
$$  

we can eliminate $\nabla \times \mathbf{A}^{T}$ from (22) to obtain  

$$
\nabla \times \mathbf { A } ^ { T } = \dot { \mathbf { B } } ^ { T } - m \mathbf { V } ^ { T } + \mu ^ { 2 } \big ( \nabla ^ { 2 } \big ) ^ { - 1 } \big ( \nabla \times \mathbf { B } ^ { T } \big ) .
$$  