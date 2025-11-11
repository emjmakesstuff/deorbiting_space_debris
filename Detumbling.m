%% Detumbling Space Debris

r_RB = 2;
m_RB = 10000;
I_RB = (1/2)*r_RB^2*m_RB;
theta_dot_RB = linspace(0,0.2,10);
F_AV = 0.1; % https://s3vi.ndc.nasa.gov/ssri-kb/static/resources/aerospace-08-00022-v3.pdf
T = (m_RB*r_RB*theta_dot_RB)/(2*F_AV);
x = (theta_dot_RB.*T*r_RB)./2;


