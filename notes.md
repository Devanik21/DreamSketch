# Wireless Communication - Comprehensive Exam Notes

---

## 1. FRIIS TRANSMISSION EQUATION

### Concept and Background
The Friis Transmission Equation, developed by Danish-American radio engineer Harald T. Friis in 1946, describes the power received by an antenna at a certain distance from a transmitting antenna under free-space (ideal) conditions. This equation establishes the fundamental relationship between transmitted power, antenna gains, wavelength, and distance, serving as the foundation for all wireless link budget calculations.

Understanding this equation is crucial because it tells us exactly how much signal power we can expect at a receiver, which directly determines whether communication is possible. Every wireless system designer uses this equation as the starting point for determining transmitter power requirements, antenna specifications, and maximum communication range.

### The Equation

$$P_r = P_t \cdot G_t \cdot G_r \cdot \left(\frac{\lambda}{4\pi d}\right)^2$$

**Where:**
- **Pᵣ** = Received power (Watts)
- **Pₜ** = Transmitted power (Watts)
- **Gₜ** = Gain of transmitting antenna (linear, not dB)
- **Gᵣ** = Gain of receiving antenna (linear, not dB)
- **λ** = Wavelength of the signal (meters) = c/f
- **d** = Distance between antennas (meters)
- **c** = Speed of light (3 × 10⁸ m/s)

### Derivation Concept
The term (λ/4πd)² represents the fraction of transmitted power captured by an isotropic receiving antenna. An isotropic antenna has an effective aperture of λ²/4π. When we transmit power Pₜ, it spreads over a sphere of surface area 4πd². The power density at distance d is Pₜ/(4πd²). Multiplying by the effective aperture gives us the received power, and including antenna gains gives the complete Friis equation.

### In Decibel Form

$$P_r(dBm) = P_t(dBm) + G_t(dB) + G_r(dB) - FSPL(dB)$$

**Free Space Path Loss (FSPL):**
$$FSPL(dB) = 20\log_{10}\left(\frac{4\pi d}{\lambda}\right) = 20\log_{10}(d) + 20\log_{10}(f) + 20\log_{10}\left(\frac{4\pi}{c}\right)$$

Simplified:
$$FSPL(dB) = 20\log_{10}(d_{km}) + 20\log_{10}(f_{MHz}) + 32.45$$

### Physical Interpretation of Each Term

**Transmitted Power (Pₜ):** The total power fed to the transmitting antenna. Higher transmit power directly increases received power linearly.

**Antenna Gains (Gₜ, Gᵣ):** Represent how well antennas focus energy in desired directions compared to an isotropic radiator. A 3 dB gain antenna delivers twice the power in its main direction compared to isotropic.

**Wavelength (λ):** Appears squared in the numerator. This is often misunderstood as meaning "higher frequencies have more loss." In reality, this term accounts for the effective aperture of the receiving antenna, which decreases with frequency for a fixed physical size.

**Distance (d):** Appears squared in the denominator, giving the inverse square law. This is because transmitted energy spreads over an ever-increasing sphere surface area (4πd²).

### Key Insights and Implications

**1. Inverse Square Law:** Received power decreases with the square of distance. Doubling the distance reduces received power by a factor of 4 (6 dB loss). This means if you can communicate at 1 km, reaching 2 km requires 4× the power or 6 dB more gain.

**2. Frequency Dependence:** The equation shows that for fixed antenna gains, higher frequencies experience greater path loss for the same distance. At 2 GHz, FSPL is 6 dB higher than at 1 GHz for the same distance. This explains why lower frequencies are preferred for long-range communication.

**3. Link Budget Equation:** The dB form is the basis of link budget analysis:
$$P_r = P_t + G_t - L_{cables} + G_r - FSPL - L_{misc}$$

### Assumptions and Limitations
The Friis equation assumes free-space propagation with no obstacles, reflections, diffraction, or atmospheric effects. It also requires that antennas are in the far-field region of each other (distance > 2D²/λ, where D is the largest antenna dimension), polarization of antennas is matched, and there are no multipath effects. In real-world scenarios, actual received power is typically much less than Friis predicts due to these factors.

### Numerical Example
**Problem:** A 900 MHz cellular system has Pₜ = 10W, Gₜ = 10 dBi, Gᵣ = 0 dBi. Find received power at 5 km.

**Solution:**
λ = c/f = 3×10⁸/900×10⁶ = 0.333 m
FSPL = 20log(4π×5000/0.333) = 20log(188,495) = 105.5 dB
Pₜ(dBm) = 10log(10×1000) = 40 dBm
Pᵣ = 40 + 10 + 0 - 105.5 = **-55.5 dBm**

---

## 2. CLASSICAL PROPAGATION MODELS

### Overview and Importance
Propagation models predict how radio signals attenuate as they travel from transmitter to receiver. While the Friis equation works for ideal free-space conditions, real wireless channels involve reflections, diffraction, scattering, and absorption. Classical propagation models account for these effects either through theoretical analysis (deterministic models) or empirical measurements (statistical models). Understanding these models is essential for cellular network planning, coverage prediction, and interference analysis.

### 2.1 Free Space Propagation Model
This is the simplest model, using the Friis equation directly. Path loss in free space is:
$$PL_{FS}(dB) = 20\log_{10}(d) + 20\log_{10}(f) - 147.55$$

This model applies to satellite links, microwave line-of-sight links, and any scenario with clear, unobstructed paths. The path loss exponent in free space is exactly 2, meaning received power decreases by 20 dB for every decade increase in distance.

### 2.2 Log-Distance Path Loss Model
This model generalizes the free-space model to account for real environments where the path loss exponent differs from 2:

$$PL(d) = PL(d_0) + 10n\log_{10}\left(\frac{d}{d_0}\right) + X_\sigma$$

**Where:**
- **PL(d₀)** = Path loss at reference distance d₀ (typically 1m or 100m), measured or calculated
- **n** = Path loss exponent (environment dependent)
- **d₀** = Reference distance (close-in measurement point)
- **Xσ** = Shadow fading component (Gaussian random variable with standard deviation σ = 4-12 dB)

The path loss exponent n captures how rapidly signal strength decreases with distance. In environments with many obstructions, n > 2, while in guided environments (like corridors), n can be less than 2.

**Typical Path Loss Exponents:**

| Environment | Path Loss Exponent (n) | Shadow Fading σ (dB) |
|-------------|------------------------|----------------------|
| Free Space | 2.0 | 0 |
| Urban (cellular) | 2.7 - 3.5 | 4-8 |
| Shadowed Urban | 3 - 5 | 6-10 |
| Indoor (LOS) | 1.6 - 1.8 | 3-6 |
| Indoor (Obstructed) | 4 - 6 | 6-12 |
| Factory (LOS) | 1.6 - 2.0 | 3-6 |
| Factory (Obstructed) | 2.0 - 3.0 | 5-8 |

**Shadow Fading (Xσ):** This log-normal random variable accounts for variations in received power due to obstacles like buildings and trees. At any given distance, the actual path loss varies randomly around the mean predicted value. The standard deviation σ determines how much variation to expect.

### 2.3 Two-Ray Ground Reflection Model
This model accounts for both the direct LOS path and a ground-reflected path, which is particularly important for large distances in relatively flat terrain:

```
[Diagram: Two-Ray Model]

    Tx ─────────────────────────────► Rx
     │╲          Direct Path         ╱│
  ht │ ╲                           ╱  │ hr
     │  ╲    Reflected Path      ╱   │
  ═══╧═══╲══════════════════════╱════╧═══
          ╲        d           ╱
           ╲__________________╱
```

**For large distances (d >> √(hₜhᵣ)):**
$$P_r = P_t G_t G_r \frac{h_t^2 h_r^2}{d^4}$$

**Key insight:** At large distances, received power falls off as d⁴ (40 dB per decade) instead of d² as in free space. This is because the direct and reflected rays nearly cancel each other at large distances, leaving only a small residual signal.

**Crossover Distance:** The distance at which the model transitions from d² to d⁴ behavior:
$$d_c = \frac{4h_t h_r}{\lambda}$$

Below this distance, free-space model applies. Above it, two-ray model applies.

### 2.4 Okumura-Hata Model
This is the most widely used empirical model for cellular system planning in urban environments. It's based on extensive measurements made by Okumura in Tokyo and later formulated into equations by Hata. Valid for frequencies 150-1500 MHz and distances 1-20 km.

**Urban Areas:**
$$L_{50}(urban) = 69.55 + 26.16\log_{10}(f_c) - 13.82\log_{10}(h_b) - a(h_m) + (44.9 - 6.55\log_{10}(h_b))\log_{10}(d)$$

**Where:**
- **fc** = Carrier frequency (150-1500 MHz)
- **hb** = Base station antenna height (30-200m)
- **hm** = Mobile antenna height (1-10m)
- **d** = Distance (1-20 km)
- **a(hm)** = Correction factor for mobile antenna height

**Mobile Antenna Correction Factor:**
For medium-small cities: $a(h_m) = (1.1\log_{10}(f_c) - 0.7)h_m - (1.56\log_{10}(f_c) - 0.8)$

For large cities: $a(h_m) = 8.29(\log_{10}(1.54h_m))^2 - 1.1$ for fc ≤ 200 MHz

**Suburban Areas:**
$$L_{50}(suburban) = L_{50}(urban) - 2[\log_{10}(f_c/28)]^2 - 5.4$$

**Open/Rural Areas:**
$$L_{50}(open) = L_{50}(urban) - 4.78[\log_{10}(f_c)]^2 + 18.33\log_{10}(f_c) - 40.94$$

### 2.5 COST-231 Hata Model
Extension of the Hata model for PCS frequencies (1500-2000 MHz):
$$L_{50} = 46.3 + 33.9\log_{10}(f_c) - 13.82\log_{10}(h_b) - a(h_m) + (44.9 - 6.55\log_{10}(h_b))\log_{10}(d) + C_m$$

Where Cm = 0 dB for medium cities and suburban, Cm = 3 dB for metropolitan centers.

### 2.6 Model Selection Guidelines
Choose Free Space model for satellite and clear LOS microwave links. Use Two-Ray model for flat rural areas with ground reflection. Apply Okumura-Hata for urban/suburban cellular planning at 150-1500 MHz. Use COST-231 for PCS/3G systems at 1800-2000 MHz. For indoor environments, use specialized indoor models with appropriate path loss exponents.

---

## 3. SELECTION COMBINING AND MAXIMAL RATIO COMBINING

### Introduction to Diversity Combining
Wireless channels suffer from multipath fading, where signal strength fluctuates rapidly due to constructive and destructive interference of multiple signal paths. Diversity techniques combat fading by providing multiple independent copies of the signal, making it unlikely that all copies fade simultaneously. Combining techniques determine how these multiple signal copies are processed to produce a single, improved output signal.

The fundamental principle is that while individual branches may experience deep fades, the probability of all branches fading simultaneously is much lower. By intelligently combining signals from multiple branches, we can dramatically improve reliability and signal quality.

### 3.1 Selection Combining (SC)

**Principle:** Select the branch (antenna) with the highest instantaneous SNR and use only that signal. This is the simplest form of diversity combining.

**Operation:**
1. Monitor SNR (or signal strength) on all M branches continuously
2. At each instant, identify the branch with maximum SNR
3. Output = signal from selected branch only (other branches ignored)
4. Switch to a different branch when it becomes stronger

```
[Diagram: Selection Combining]

Branch 1 ──►[Measure SNR]──┐
                          │
Branch 2 ──►[Measure SNR]──┼──►[SELECT MAX]──► Output
                          │
Branch M ──►[Measure SNR]──┘

    Only ONE branch connected to output at any time
```

**Mathematical Expression:**
$$\gamma_{SC} = \max(\gamma_1, \gamma_2, ..., \gamma_M)$$

Where γᵢ is the instantaneous SNR of branch i.

**Statistical Analysis (for i.i.d. Rayleigh fading):**

The CDF (probability that output SNR is less than threshold γ) is:
$$P(\gamma_{SC} < \gamma) = \prod_{i=1}^{M} P(\gamma_i < \gamma) = \left[1 - e^{-\gamma/\bar{\gamma}}\right]^M$$

This expression shows that the probability of being below a threshold decreases exponentially with the number of branches.

**Outage Probability Improvement:**
For a single branch, outage probability at threshold γth is: P₁ = 1 - e^(-γth/γ̄)
For M branches with SC, outage probability becomes: PM = [P₁]^M

Example: If P₁ = 0.1 (10% outage), then for M=4 branches, P₄ = (0.1)⁴ = 0.0001 (0.01% outage)

**Average SNR Improvement:**
$$\bar{\gamma}_{SC} = \bar{\gamma} \sum_{k=1}^{M} \frac{1}{k} = \bar{\gamma}\left(1 + \frac{1}{2} + \frac{1}{3} + ... + \frac{1}{M}\right)$$

For M=2: γ̄SC = 1.5γ̄ (1.76 dB gain)
For M=4: γ̄SC = 2.08γ̄ (3.18 dB gain)

**Advantages of Selection Combining:**
Simple implementation requiring only one RF chain for processing after selection. No co-phasing required since only one signal is used. Low complexity and cost make it suitable for mobile handsets. Works well even with imperfect channel estimation.

**Disadvantages of Selection Combining:**
Does not fully utilize all available signal energy since M-1 branches are discarded. Suboptimal compared to MRC. Switching transients may cause brief disturbances. Continuous monitoring of all branches required.

### 3.2 Maximal Ratio Combining (MRC)

**Principle:** Combine all branch signals with optimal weights that are proportional to their individual SNRs (or channel gain magnitudes). This maximizes the output SNR and is proven to be the optimal linear combining technique.

**Operation:**
1. Estimate channel coefficient hᵢ for each branch
2. Co-phase all branch signals (align phases by multiplying by hᵢ*)
3. Weight each branch proportionally to its SNR: wᵢ = hᵢ*/σₙ²
4. Sum all weighted, co-phased signals

```
[Diagram: Maximal Ratio Combining]

Branch 1 ──►[×h₁*]──►[Weight w₁]──┐
                                  │
Branch 2 ──►[×h₂*]──►[Weight w₂]──┼──►[Σ SUM]──► Output
                                  │
Branch M ──►[×hₘ*]──►[Weight wₘ]──┘

    ALL branches contribute to output
    Weights proportional to channel quality
```

**Mathematical Expression:**

Received signal on branch i: rᵢ = hᵢ·s + nᵢ

MRC output:
$$y_{MRC} = \sum_{i=1}^{M} w_i \cdot r_i = \sum_{i=1}^{M} h_i^* \cdot r_i$$

The optimal weights are: $w_i = \frac{h_i^*}{\sigma_n^2}$ (conjugate of channel coefficient divided by noise variance)

**Output SNR:**
$$\gamma_{MRC} = \sum_{i=1}^{M} \gamma_i = \sum_{i=1}^{M} \frac{|h_i|^2 E_s}{\sigma_n^2}$$

This remarkable result shows that MRC output SNR is simply the **sum** of all individual branch SNRs!

**Average SNR (for i.i.d. Rayleigh fading):**
$$\bar{\gamma}_{MRC} = M \cdot \bar{\gamma}$$

This is a linear gain with the number of branches. Each doubling of branches adds 3 dB.

**Diversity Order:**
MRC achieves full diversity order of M. The BER at high SNR decreases as (1/SNR)^M, meaning each additional branch provides another order of protection against fading.

**Key Result:** MRC provides the **maximum possible SNR** among all linear combining techniques. No other linear combiner can do better. This optimality comes from the matched filter principle, where the weights are matched to the channel coefficients.

**Implementation Requirements:**
MRC requires accurate channel estimation for all branches, co-phasing capability to align signal phases, M complete RF receive chains, and more processing power for weight calculation.

### 3.3 Equal Gain Combining (EGC)
A practical compromise between SC and MRC where all branches are co-phased and added with equal weights:
$$y_{EGC} = \sum_{i=1}^{M} e^{-j\phi_i} \cdot r_i$$

Performance is within 1 dB of MRC but doesn't require amplitude estimation.

### 3.4 Comprehensive Comparison Table

| Parameter | Selection Combining | Maximal Ratio Combining |
|-----------|--------------------|-----------------------|
| Complexity | Low | High |
| RF chains needed | 1 (after selection) | M (parallel processing) |
| Co-phasing | Not required | Required |
| Channel estimation | Envelope only | Amplitude and phase |
| Average SNR gain | γ̄·Σ(1/k) | M·γ̄ |
| SNR gain (M=4) | 2.08γ̄ | 4γ̄ |
| Diversity order | M | M |
| Optimality | Suboptimal | Optimal (among linear) |
| Cost | Lower | Higher |
| Power consumption | Lower | Higher |
| Typical application | Mobile handsets | Base stations |

---

## 4. ADVANTAGES OF RAKE RECEIVER

### What is a RAKE Receiver?
A RAKE receiver is a specialized radio receiver designed specifically for spread spectrum systems (particularly CDMA) to combat and exploit multipath propagation. The name "RAKE" comes from the analogy of a garden rake collecting leaves. Just as a rake gathers multiple leaves with its tines, a RAKE receiver uses multiple "fingers" to separately detect, track, and coherently combine multipath signal components that arrive at different times.

In conventional narrowband systems, multipath causes intersymbol interference (ISI) and fading that degrades performance. However, in spread spectrum systems, the wide bandwidth allows multipath components separated by more than one chip period to be resolved and treated as independent signals. The RAKE receiver exploits this property to turn a wireless channel's multipath nature from a problem into an advantage.

### RAKE Receiver Architecture

```
[Diagram: Detailed RAKE Receiver Structure]

                    ┌─────────────────────────────────────┐
                    │         RAKE RECEIVER               │
Received            │                                     │
Spread   ┌──────────┼─────────────────────────────────────┼───┐
Spectrum │          │  ┌────────┐   ┌────────┐   ┌─────┐ │   │
Signal ──┼─────────►│  │Finger 1│──►│Correlator──►│Delay│ │   │
         │          │  │  (τ₁)  │   │   PN     │   │ Adj │─┼─┐ │
         │          │  └────────┘   └────────┘   └─────┘ │ │ │
         │          │  ┌────────┐   ┌────────┐   ┌─────┐ │ │ │
         ├─────────►│  │Finger 2│──►│Correlator──►│Delay│─┼─┤ │
         │          │  │  (τ₂)  │   │   PN     │   │ Adj │ │ │ │
         │          │  └────────┘   └────────┘   └─────┘ │ │ │
         │          │  ┌────────┐   ┌────────┐   ┌─────┐ │ │ │
         └─────────►│  │Finger 3│──►│Correlator──►│Delay│─┼─┤ │
                    │  │  (τ₃)  │   │   PN     │   │ Adj │ │ │ │
                    │  └────────┘   └────────┘   └─────┘ │ │ │
                    │                                     │ │ │
                    │         ┌─────────────────┐        │ │ │
                    │         │   MRC Combiner  │◄───────┼─┘ │
                    │         │  (Weighted Sum) │        │   │
                    │         └────────┬────────┘        │   │
                    │                  │                 │   │
                    └──────────────────┼─────────────────┘   │
                                       ▼                     │
                               Combined Output ◄─────────────┘
```

**Finger Operation:** Each finger contains a correlator synchronized to a specific multipath delay. The correlator despreads the signal by multiplying with a time-aligned copy of the PN code. After despreading, the signal is passed through a channel estimator to determine amplitude and phase, then combined using MRC.

### Detailed Advantages of RAKE Receiver

**1. Multipath Diversity Exploitation**
Instead of treating multipath as harmful interference, the RAKE receiver constructively combines multipath components. Each resolvable multipath component (separated by more than one chip period Tc = 1/Rc) is tracked by a separate finger. When L multipath components are resolved and combined using MRC, the output SNR becomes:
$$\gamma_{RAKE} = \sum_{l=1}^{L} \gamma_l$$

This provides diversity gain of order L without requiring multiple antennas. In rich multipath environments, this can provide 10-15 dB of improvement over a single-path receiver.

**2. Improved Signal Quality and Reliability**
The probability of deep fading is dramatically reduced. If one path experiences a deep fade, other paths likely remain strong. The probability that all L paths simultaneously fade below threshold γ is:
$$P_{outage} = \prod_{l=1}^{L} P(\gamma_l < \gamma) = [P_{single}]^L$$

For example, if single-path outage probability is 10%, with L=3 paths it becomes 0.1%. This translates to more reliable voice calls and higher data throughput.

**3. No Complex Equalizer Required**
In narrowband systems, multipath causes ISI that requires complex adaptive equalizers (Viterbi equalizers, decision feedback equalizers) with high computational cost. In spread spectrum with RAKE, the PN code's autocorrelation properties naturally separate multipath components. The processing gain inherently handles multipath without explicit equalization, greatly simplifying receiver design.

**4. Soft Handoff Capability (Macro-Diversity)**
RAKE fingers can simultaneously track signals from multiple base stations during handoff. When a mobile moves from one cell to another:
- Some fingers track the serving base station
- Other fingers track the target base station  
- MRC combines signals from both sources

This "make before break" soft handoff provides seamless service without the brief interruption of hard handoff. The diversity from multiple base stations also improves signal quality in the overlap region.

**5. Resistance to Narrowband Interference**
The spread spectrum processing provides inherent interference rejection. After despreading, the desired signal is concentrated while narrowband interference is spread across the bandwidth:
$$SNR_{improvement} = \frac{W_{spread}}{W_{signal}} = G_p = \frac{R_c}{R_b}$$

A typical CDMA system with Gp = 128 provides 21 dB of narrowband interference rejection.

**6. Time Diversity Utilization**
Multipath components arriving at different delays effectively provide time diversity. The RAKE receiver captures and combines these time-diverse copies. This is particularly valuable in slowly-fading channels where traditional time-interleaving would introduce unacceptable delay.

**7. Near-Far Problem Mitigation**
When combined with power control, RAKE helps maintain reliable communication even with varying user distances. The diversity gain provides margin against imperfect power control, while the processing gain rejects interference from nearby strong users.

**8. Efficient Spectrum Utilization Through CDMA**
Multiple users share the same frequency band using different spreading codes. The RAKE receiver enables reliable individual signal recovery despite mutual interference:
$$Capacity = \frac{W/R}{E_b/N_0} \times \frac{1}{1 + f} \times G_v \times G_s$$

Where f = other-cell interference factor, Gv = voice activity gain, Gs = sectorization gain.

**9. Path Tracking and Adaptation**
Modern RAKE receivers include searcher fingers that continuously scan for new multipath components. When the channel changes (due to mobility or environment), the receiver adapts by reassigning fingers to track the strongest current paths.

**10. Graceful Degradation**
Even if some fingers lose lock or track weak paths, remaining fingers continue providing useful output. The system degrades gradually rather than failing catastrophically, improving overall system reliability.

---

## 5. TRAFFIC CHARACTERISTICS AND DISTRIBUTION PATTERNS

### Introduction to Teletraffic Engineering
Teletraffic engineering is the science of predicting and planning for communication traffic to ensure networks can handle demand while meeting quality of service targets. Understanding traffic characteristics is essential for network dimensioning, where planners must determine how many channels, servers, or bandwidth to deploy. This section covers the statistical properties of traffic and how it varies over time and space.

### 5.1 Typical Traffic Characteristics

**1. Call Arrival Process**
In telephony networks, calls arrive randomly following a **Poisson process**. This means arrivals are independent of each other (one call arriving doesn't affect when the next arrives), arrivals occur uniformly in time with no clustering, and the probability of two arrivals in an infinitesimally small interval is negligible.

The arrival rate λ (calls per unit time) varies with time of day but is considered constant during short analysis periods. Inter-arrival times follow an exponential distribution with PDF:
$$f(t) = \lambda e^{-\lambda t}, \quad t \geq 0$$

Mean inter-arrival time = 1/λ

**2. Call Holding Time (Duration)**
The duration of calls follows an **exponential distribution** with mean holding time h = 1/μ:
$$f(t) = \mu e^{-\mu t}, \quad t \geq 0$$

Typical mean holding times: Voice calls average 90-120 seconds, data sessions vary widely from seconds to hours, SMS/signaling messages last only milliseconds.

The exponential distribution has the memoryless property: the probability of a call ending in the next minute is the same regardless of how long the call has already lasted. While real call durations may deviate from exponential, this model provides tractable analysis and good approximations.

**3. Traffic Intensity (Offered Load)**
Traffic intensity A, measured in Erlangs, represents the average number of simultaneous calls:
$$A = \lambda \times h = \frac{\lambda}{\mu} \text{ (Erlangs)}$$

One Erlang represents one circuit (channel) continuously occupied for the measurement period (typically one hour). If 30 calls are made per hour and each lasts 6 minutes (0.1 hour), traffic is 30 × 0.1 = 3 Erlangs.

**4. Busy Hour Traffic**
Network dimensioning uses the peak traffic period, called the **Busy Hour**, which is typically the 60-minute period with highest traffic. Busy Hour Call Attempts (BHCA) measures server load. Networks are designed for busy hour traffic to ensure acceptable service during peak demand while accepting that resources are underutilized during off-peak times.

**5. Traffic Measurement Parameters**
**Offered traffic (A):** Total traffic demand from users attempting to use the network. This includes both successful and blocked calls.

**Carried traffic (C):** Traffic actually served by the network. C = A × (1 - PB), where PB is blocking probability.

**Blocked traffic:** Traffic that cannot be served due to congestion. Equals A - C.

**Grade of Service (GoS):** Probability that a call is blocked (for circuit-switched) or delayed beyond threshold (for packet-switched). Target GoS is typically 1-2% for voice networks.

### 5.2 Traffic Distribution Patterns

**Temporal Distribution (Time-of-Day Variation):**
Traffic follows predictable daily patterns influenced by human activity:

```
[Diagram: Daily Traffic Pattern]

Traffic │         ╭──╮        ╭──╮
Intensity│        ╱    ╲      ╱    ╲
(Erlangs)│   ╭──╮╱      ╲    ╱      ╲
        │  ╱    ╲        ╲──╱        ╲
        │ ╱      ╲                    ╲
        │╱                             ╲
        └──────────────────────────────────►
         0  3  6  9  12  15  18  21  24
                    Hour of Day

    Morning Peak (9-11 AM): Business calls
    Afternoon Lull (12-2 PM): Lunch time
    Afternoon Peak (2-5 PM): Business calls
    Evening Peak (7-9 PM): Residential calls
    Night Minimum (2-6 AM): Sleep time
```

**Weekly patterns:** Business traffic peaks on weekdays, residential peaks on weekends. Monday mornings and Friday afternoons often have distinctive patterns.

**Seasonal patterns:** Holiday periods show different patterns. Shopping seasons affect retail area traffic. Summer vacations reduce business district traffic.

**Spatial Distribution (Geographic Variation):**

Traffic is not uniformly distributed across a coverage area. Understanding spatial patterns is crucial for cell planning:

**Uniform distribution:** An idealized assumption where all cells experience equal traffic. Used for initial planning but rarely reflects reality.

**Non-uniform distribution:** Real networks show significant spatial variation with hotspots (shopping malls, stadiums, airports, train stations, business districts) generating 5-10× average traffic density. Residential areas show moderate, predictable traffic. Rural areas have sparse traffic. Special events (concerts, sports) create temporary extreme hotspots.

**Mobility patterns:** Rush hours create directional traffic flows (morning: suburbs→city center, evening: reverse). Highways experience mobile traffic requiring careful handoff planning. Public transit corridors show concentrated mobile traffic.

```
[Diagram: Spatial Traffic Distribution]

    ┌─────────────────────────────────────────┐
    │    Low     │  Medium  │     Low        │
    │   (Rural)  │(Suburban)│   (Rural)      │
    ├────────────┼──────────┼────────────────┤
    │   Medium   │██HIGH██ │    Medium      │
    │ (Suburban) │(Business)│  (Suburban)    │
    ├────────────┼──────────┼────────────────┤
    │    Low     │  Medium  │     Low        │
    │  (Rural)   │(Suburban)│   (Rural)      │
    └─────────────────────────────────────────┘
    
    Cell sizes adjusted: Smaller cells in high-traffic areas
```

### 5.3 Traffic Types and Their Characteristics

**1. Voice Traffic (Circuit-Switched)**
Voice traffic is characterized by constant bit rate (e.g., 12.2 kbps for AMR), predictable holding times averaging 90-120 seconds, strict delay requirements under 150ms one-way, and Poisson arrival patterns well-modeled by Erlang formulas.

**2. Data Traffic (Packet-Switched)**
Data traffic differs significantly with bursty, variable bit rate patterns, heavy-tailed session durations (many short, few very long), tolerance for delay but sensitivity to throughput, and self-similar patterns not well-modeled by Poisson (requires different models like Pareto).

**3. Signaling Traffic**
Control plane messages for call setup, handoff, and location updates comprise typically 5-10% of total traffic. Signaling has very short message durations measured in milliseconds, critical reliability requirements, and peaks during call setup attempts which may not correlate with voice traffic peaks.

**4. Machine-to-Machine (M2M) / IoT Traffic**
This emerging traffic type features massive numbers of devices with infrequent, small transmissions, synchronized behavior that may cause traffic spikes (e.g., smart meters reporting simultaneously), and different QoS requirements than human-generated traffic.

### 5.4 Traffic Modeling for Network Planning

**Busy Hour Determination:**
Identify the time-consistent busy hour (same hour each day) or bouncing busy hour (different peak hours). Design for busy hour traffic with appropriate GoS target.

**Forecasting:**
Project future traffic based on subscriber growth (typically 10-30% annually), usage per subscriber trends, new services impact, and seasonal adjustments.

**Dimensioning Process:**
1. Estimate busy hour offered traffic per cell
2. Apply Erlang B (or appropriate model) to determine channels needed
3. Add margin for growth and uncertainty
4. Verify interference and coverage constraints

---

## 6. HANDOVER/HANDOFF PROCESSING AND STAGES (10 Marks)

### Definition and Importance
**Handover (Handoff)** is the process of transferring an ongoing call or data session from one cell (base station) to another as the mobile user moves across cell boundaries. This is one of the most critical functions in cellular systems, distinguishing them from simple radio systems. Without effective handover, calls would drop every time a user crossed a cell boundary, making the system unusable for mobile users.

The handover process must be fast enough to be imperceptible to users (typically under 200ms interruption), reliable enough to maintain call quality, and efficient enough to minimize signaling overhead. Poor handover performance directly impacts customer satisfaction and network efficiency.

### Types of Handover

**1. Hard Handover (Break-Before-Make)**
In hard handover, the connection to the old base station is broken before establishing the new connection. This creates a brief interruption but simplifies resource management.

Characteristics: Used in FDMA and TDMA systems (GSM, EDGE), brief interruption possible (typically 100-200ms), simpler implementation, mobile communicates with only one BS at a time, and frequency change usually required.

**2. Soft Handover (Make-Before-Break)**
In soft handover, the mobile maintains simultaneous connections to multiple base stations during the transition. The old connection is released only after the new connection is stable.

Characteristics: Used in CDMA systems (IS-95, CDMA2000, WCDMA), seamless transition with no interruption, more complex implementation, requires same frequency on both cells (possible in CDMA), provides macro-diversity gain during handover region, and typically 30-40% of calls in soft handover at any time.

**3. Softer Handover**
Handover between sectors of the same cell site. Since both sectors are controlled by the same base station, this is handled locally without MSC involvement. The BS combines signals from both sectors using MRC, simpler than soft handover.

**4. Inter-System Handover (Vertical Handover)**
Handover between different radio access technologies:
- 4G LTE to 3G WCDMA (for voice calls before VoLTE)
- 5G to 4G fallback
- WiFi to cellular

This is the most complex type, requiring coordination between different systems, different protocols, and possibly different core networks.

**5. Intra-cell Handover**
Change of channel within the same cell, typically to avoid interference or improve quality. No change of serving base station.

### Handover Processing Stages

The handover process consists of three main stages: Measurement, Decision, and Execution.

```
[Diagram: Complete Handover Process Flow]

┌──────────────────────────────────────────────────────────────────┐
│                    HANDOVER PROCESS                              │
├──────────────────┬───────────────────┬───────────────────────────┤
│     STAGE 1      │      STAGE 2      │         STAGE 3           │
│   MEASUREMENT    │     DECISION      │        EXECUTION          │
├──────────────────┼───────────────────┼───────────────────────────┤
│                  │                   │                           │
│ • MS measures    │ • Compare signal  │ • Resource allocation     │
│   serving cell   │   strengths       │   in target cell          │
│                  │                   │                           │
│ • MS measures    │ • Apply hysteresis│ • Signaling exchange      │
│   neighbor cells │   and thresholds  │   (HO command)            │
│                  │                   │                           │
│ • Filter/average │ • Dwell timer     │ • MS tunes to new         │
│   measurements   │   check           │   channel                 │
│                  │                   │                           │
│ • Report to BS   │ • Select target   │ • Path switching at       │
│                  │   cell            │   MSC                     │
│                  │                   │                           │
│ Duration:        │ Duration:         │ Duration:                 │
│ Continuous       │ ~100ms            │ ~100-300ms                │
└──────────────────┴───────────────────┴───────────────────────────┘
```

### Stage 1: Measurement Phase (Detailed)

The measurement phase is continuous throughout the call duration. The mobile station and network constantly monitor signal quality to prepare for potential handovers.

**Mobile Station (MS) Measurements:**

**Received Signal Strength Indicator (RSSI):** Measures total power received on a channel, including signal, interference, and noise. Easy to measure but doesn't distinguish between signal and interference.

**Reference Signal Received Power (RSRP) [LTE]:** Measures power of specific reference signals, giving true signal strength independent of interference and bandwidth.

**Signal-to-Interference Ratio (SIR) or SINR:** Ratio of desired signal to interference plus noise. Better indicator of actual link quality than RSSI alone.

**Bit Error Rate (BER):** Measures transmission quality by counting errors. Higher BER indicates degrading link.

**Frame Error Rate (FER):** Percentage of frames with uncorrectable errors. Directly impacts user-perceived quality.

**Measurement Process:**
1. MS continuously monitors serving cell signal strength and quality
2. MS periodically scans neighbor cell pilots/beacons (from neighbor list provided by network)
3. Measurements are averaged over a time window (typically 480ms to 5 seconds)
4. Averaging reduces rapid fluctuations due to fast fading
5. Measurement reports sent to serving BS periodically or when thresholds crossed

**Key Measurement Parameters:**
- **Measurement interval:** How often measurements are taken (e.g., every 480ms in GSM)
- **Averaging window (L):** Number of samples averaged to reduce noise (e.g., 4-8 samples)
- **Reporting mode:** Periodic or event-triggered
- **Neighbor list:** List of cells to measure (typically 6-32 neighbors)

**Measurement Filtering:**
Raw measurements are filtered using Layer 3 filtering:
$F_n = (1-a) \times F_{n-1} + a \times M_n$

Where Fn is filtered value, Mn is new measurement, and a is filter coefficient (0 < a ≤ 1).

### Stage 2: Decision Phase (Detailed)

The decision phase determines IF and WHEN a handover should occur, and to which target cell. This phase must balance between unnecessary handovers (ping-pong) and delayed handovers (call drops).

**Handover Decision Criteria:**

**1. Relative Signal Strength (Most Common):**
Handover when neighbor signal strength exceeds serving cell by a margin:
$S_{neighbor} > S_{serving} + Hysteresis$

**2. Relative Signal Strength with Threshold:**
$S_{neighbor} > S_{serving} + H \text{ AND } S_{serving} < Threshold$

Only consider handover when serving signal is below an acceptable threshold, preventing unnecessary handovers when current signal is adequate.

**3. Relative Signal Strength with Hysteresis and Dwell Timer:**
$S_{neighbor} > S_{serving} + H \text{ for duration } T_{dwell}$

The neighbor must be stronger for a sustained period before handover is triggered.

**4. SIR-Based Decision:**
More reliable in interference-limited systems:
$SIR_{neighbor} > SIR_{serving} + H$

**Hysteresis and Its Importance:**

```
[Diagram: Handover Decision with Hysteresis]

Signal     │
Strength   │  Serving Cell        Target Cell
(dBm)      │      ╲                  ╱
   -60 ────│───────╲────────────────╱───────
           │        ╲              ╱
   -70 ────│─────────╲────────────╱─────────
           │          ╲    ↑H    ╱
   -80 ────│───────────╲──────╱─────────────
           │            ╲    ╱
   -90 ────│─────────────╲──╱───────────────
           │              ╲╱← Actual HO point
  -100 ────│──────────────╳─────────────────
           │             ╱╲
           └──────────────────────────────────►
                    Cell Boundary    Distance
           
    Without hysteresis: HO at boundary → ping-pong
    With hysteresis H: HO delayed → stable
```

**Hysteresis margin (H):** Typically 2-6 dB. Prevents ping-pong effect where mobile rapidly alternates between cells when near the boundary. Too small causes ping-pong; too large causes delayed handover and potential call drops.

**Dwell Timer (Time-to-Trigger):** Ensures signal from new cell is consistently stronger for a minimum time (e.g., 320ms to 5.12s) before triggering handover. Filters out temporary signal fluctuations due to fast fading.

**Handover Decision Algorithm:**
```
IF (serving_signal < threshold_min) THEN
    Initiate urgent handover (call may drop)
ELSE IF (neighbor_signal > serving_signal + hysteresis) THEN
    IF (condition sustained for dwell_time) THEN
        IF (target_cell has available channels) THEN
            Initiate handover to target
        ELSE
            Try next best candidate
        ENDIF
    ENDIF
ENDIF
```

**Target Cell Selection:**
When multiple neighbors qualify for handover, select based on: highest signal strength, lowest traffic load, appropriate frequency layer, and priority settings (e.g., prefer macro cells over small cells).

### Stage 3: Execution Phase (Detailed)

Once the decision is made, the execution phase actually transfers the call to the new cell. This must happen quickly to minimize disruption.

**Step 1: Resource Allocation**
The serving BS/MSC sends a handover request to the target BS containing mobile identity, call parameters, required resources, and security information. The target BS attempts to allocate a traffic channel. If no channel is available, the target BS may queue the request or reject it (causing handover blocking or queuing the handover request).

**Step 2: Signaling Exchange**
Once resources are allocated in the target cell, handover command is sent to MS containing new frequency and timeslot (FDMA/TDMA), new scrambling code (CDMA), timing advance for new cell, power level to use, and encryption keys if changed.

**Step 3: Connection Transfer**
The MS executes the handover by tuning to the new channel/frequency, adjusting timing and power as commanded, sending a handover access burst to the target BS (to synchronize timing), and target BS confirms successful receipt.

**Step 4: Path Switching**
The MSC switches the voice/data path from old BS to new BS. The old channel is released, context (ciphering state, etc.) is transferred, and the call continues on the new channel.

```
[Diagram: Handover Execution Signaling (GSM)]

    MS              Old BSS           MSC           New BSS
     │                │                │               │
     │ Meas Report    │                │               │
     │───────────────►│                │               │
     │                │ HO Required    │               │
     │                │───────────────►│               │
     │                │                │ HO Request    │
     │                │                │──────────────►│
     │                │                │               │ Allocate
     │                │                │               │ Channel
     │                │                │ HO Ack        │
     │                │                │◄──────────────│
     │                │ HO Command     │               │
     │                │◄───────────────│               │
     │ HO Command     │                │               │
     │◄───────────────│                │               │
     │                                                 │
     │═══════════════════════════════════════════════►│
     │           (Tune to new channel)                │
     │                                                 │
     │ HO Access                                       │
     │────────────────────────────────────────────────►│
     │                                                 │
     │ Physical Info                                   │
     │◄────────────────────────────────────────────────│
     │                │                │               │
     │ HO Complete    │                │               │
     │────────────────────────────────────────────────►│
     │                │                │ HO Complete   │
     │                │                │◄──────────────│
     │                │ Clear Command  │               │
     │                │◄───────────────│               │
     │                │                │               │
     
     Total Duration: 100-500ms (hard handover)
```

**Timing Constraints:**
- Total hard handover duration: 100-500ms
- Soft handover: No interruption (continuous diversity)
- Maximum acceptable voice interruption: ~200ms (imperceptible)
- Typical GSM handover: ~200ms
- Typical LTE handover: ~50ms (due to preparation in advance)

### Handover Failure Causes and Mitigation

**1. No Available Channel in Target Cell (Handover Blocking)**
Mitigation: Reserve channels for handover (guard channels), priority queuing for handover requests, and dynamic channel allocation.

**2. Signal Degrades Too Rapidly**
Mitigation: Reduce hysteresis and dwell time in fast-fading environments, use predictive algorithms, and implement fast handover mechanisms.

**3. Signaling Failure**
Mitigation: Robust signaling protocols with retransmission, adequate signaling channel capacity.

**4. Timing Synchronization Failure**
Mitigation: Accurate timing advance calculation, pilot signal design for quick synchronization.

**5. Wrong Target Cell Selection**
Mitigation: Include multiple candidates in handover preparation, use SIR-based decisions in interference-limited scenarios.

### Handover Performance Metrics

**Handover Success Rate:** Percentage of attempted handovers that complete successfully. Target: >99%.

**Handover Failure Rate:** 1 - Success Rate. Should be <1%.

**Call Drop Rate Due to Handover:** Calls lost during handover attempt. Should be <0.5%.

**Ping-Pong Rate:** Percentage of handovers followed by rapid return to original cell. Indicates hysteresis too small.

**Handover Delay:** Time from trigger to completion. Should be <500ms for hard handover.

**Unnecessary Handover Rate:** Handovers that could have been avoided. Wastes resources.

---

## 7. OFDM, SUBCARRIER ORTHOGONALITY, AND DSSS

### 7.1 Orthogonal Frequency Division Multiplexing (OFDM)

**Definition and Motivation:**
OFDM is a multicarrier modulation technique that divides a high-rate data stream into multiple lower-rate streams, each transmitted simultaneously on a separate orthogonal subcarrier. The fundamental motivation is to combat frequency-selective fading, which occurs when the channel bandwidth exceeds the coherence bandwidth.

In a wideband single-carrier system, multipath causes intersymbol interference (ISI) because delayed copies of previous symbols interfere with current symbols. OFDM solves this by converting one frequency-selective fading channel into many flat-fading narrowband subchannels, extending symbol duration so that delay spread is a small fraction of symbol time, and using a cyclic prefix to eliminate residual ISI.

**Key Principle:** Each subcarrier experiences flat fading (constant channel gain across its narrow bandwidth), even when the overall channel is frequency-selective. This greatly simplifies equalization since each subcarrier needs only a single complex multiplication rather than a complex time-domain equalizer.

```
[Diagram: OFDM Spectrum vs Single Carrier]

SINGLE CARRIER:
Power  │    ┌───────────────────────┐
Density│    │                       │
       │    │   Wideband Signal     │
       │    │                       │
       │────┴───────────────────────┴────────►
                    Frequency
       Entire band affected by frequency-selective fading

OFDM:
Power  │  ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐
Density│  │ │ │ │ │ │ │ │ │ │ │ │ │ │ │ │
       │  │ │ │ │ │ │ │ │ │ │ │ │ │ │ │ │
       │──┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴──►
          f₀  f₁  f₂  f₃  f₄  f₅  f₆  f₇
       Each subcarrier experiences flat fading
       Subcarriers overlap but don't interfere (orthogonal)
```

**OFDM System Block Diagram:**
```
TRANSMITTER:
                ┌───────┐   ┌──────┐   ┌────────┐   ┌─────┐   ┌────┐
Data ──►[S/P]──►│ QAM   │──►│ IFFT │──►│Add CP  │──►│ DAC │──►│ RF │──►
    bits        │Mapping│   │(N-pt)│   │        │   │     │   │ Tx │
                └───────┘   └──────┘   └────────┘   └─────┘   └────┘
                     │           │
              N symbols    Time-domain
              (frequency)  OFDM symbol

RECEIVER:
    ┌────┐   ┌─────┐   ┌────────┐   ┌──────┐   ┌───────┐   ┌─────┐
───►│ RF │──►│ ADC │──►│Remove  │──►│ FFT  │──►│Channel│──►│ QAM │──►[P/S]──► Data
    │ Rx │   │     │   │  CP    │   │(N-pt)│   │ Equal │   │Demap│         bits
    └────┘   └─────┘   └────────┘   └──────┘   └───────┘   └─────┘
```

**OFDM Signal (Time Domain):**
The transmitted OFDM signal in one symbol period is:
$s(t) = \sum_{k=0}^{N-1} X_k \cdot e^{j2\pi f_k t} = \sum_{k=0}^{N-1} X_k \cdot e^{j2\pi k \Delta f \cdot t}, \quad 0 \leq t \leq T_s$

Where:
- **N** = Number of subcarriers (typically 64, 256, 1024, 2048)
- **Xk** = Complex data symbol on k-th subcarrier (QAM/PSK)
- **fk** = Frequency of k-th subcarrier = f₀ + k·Δf
- **Δf** = Subcarrier spacing
- **Ts** = OFDM symbol duration (excluding cyclic prefix)

**IFFT Implementation:**
The OFDM signal can be generated using Inverse FFT:
$s[n] = \frac{1}{N}\sum_{k=0}^{N-1} X_k \cdot e^{j2\pi kn/N}, \quad n = 0, 1, ..., N-1$

This is exactly the IFFT of the frequency-domain symbols {Xk}, making OFDM computationally efficient.

**Key OFDM Parameters:**

| Parameter | Symbol | Relationship |
|-----------|--------|--------------|
| Number of subcarriers | N | System design choice |
| Subcarrier spacing | Δf | Δf = 1/Ts |
| Symbol duration | Ts | Ts = 1/Δf |
| Total bandwidth | B | B ≈ N × Δf |
| Cyclic prefix duration | Tcp | Tcp > τmax (max delay spread) |
| Total symbol time | Tsym | Tsym = Ts + Tcp |

**Example (LTE):**
- N = 2048 subcarriers (20 MHz bandwidth)
- Δf = 15 kHz
- Ts = 1/15000 = 66.67 μs
- Tcp = 4.69 μs (normal CP)
- Tsym = 71.36 μs

### 7.2 Subcarrier Orthogonality - Mathematical Derivation

**Orthogonality Condition:**
Two signals are orthogonal if their inner product over the observation interval equals zero. For OFDM subcarriers:

$\int_0^{T_s} e^{j2\pi f_m t} \cdot e^{-j2\pi f_n t} \, dt = \begin{cases} T_s & \text{if } m = n \\ 0 & \text{if } m \neq n \end{cases}$

**Detailed Mathematical Proof:**

For subcarriers m and n with frequencies fm = f₀ + m·Δf and fn = f₀ + n·Δf:

$I_{mn} = \int_0^{T_s} e^{j2\pi f_m t} \cdot e^{-j2\pi f_n t} \, dt = \int_0^{T_s} e^{j2\pi (f_m - f_n) t} \, dt$

$= \int_0^{T_s} e^{j2\pi (m-n)\Delta f \cdot t} \, dt$

Let k = m - n (an integer for different subcarriers):

$I_{mn} = \int_0^{T_s} e^{j2\pi k \Delta f \cdot t} \, dt$

**Case 1: m = n (same subcarrier, k = 0)**
$I_{mm} = \int_0^{T_s} e^{0} \, dt = \int_0^{T_s} 1 \, dt = T_s$

**Case 2: m ≠ n (different subcarriers, k ≠ 0)**
$I_{mn} = \left[\frac{e^{j2\pi k \Delta f \cdot t}}{j2\pi k \Delta f}\right]_0^{T_s} = \frac{e^{j2\pi k \Delta f \cdot T_s} - 1}{j2\pi k \Delta f}$

For this to equal zero, we need:
$e^{j2\pi k \Delta f \cdot T_s} = 1$

This occurs when:
$k \Delta f \cdot T_s = \text{integer}$

Since k is already an integer, we need:
$\boxed{\Delta f \cdot T_s = 1 \implies \Delta f = \frac{1}{T_s}}$

**This is the fundamental orthogonality condition for OFDM!**

**Physical Interpretation:**
When Δf = 1/Ts, each subcarrier completes exactly an integer number of cycles more than its neighbor during one symbol period. When we integrate (correlate) the received signal with each subcarrier, only the matching subcarrier produces a non-zero output due to the zeros of the sinc function in the frequency domain.

```
[Diagram: Orthogonal Subcarriers in Frequency Domain]

         │ Subcarrier 0    Subcarrier 1    Subcarrier 2
Spectrum │      │              │               │
         │     ╱│╲            ╱│╲             ╱│╲
         │    ╱ │ ╲          ╱ │ ╲           ╱ │ ╲
         │   ╱  │  ╲        ╱  │  ╲         ╱  │  ╲
         │  ╱   │   ╲      ╱   │   ╲       ╱   │   ╲
         │──────┼────╲────╱────┼────╲────╱────┼────────►
         │      f₀    ╲  ╱     f₁    ╲  ╱     f₂     Freq
         │             ╲╱             ╲╱
         │              Zero at       Zero at
         │              neighbor      neighbor
         
    Peak of each subcarrier occurs at zero-crossing of neighbors
    → Zero interference despite spectral overlap
```

### 7.3 Cyclic Prefix (CP) - Detailed Explanation

**Purpose:** The cyclic prefix is a guard interval that eliminates Inter-Symbol Interference (ISI) and preserves subcarrier orthogonality in multipath channels.

**How CP Works:**
1. After IFFT, copy the last Ncp samples of the OFDM symbol
2. Prepend these samples to the beginning of the symbol
3. This creates a "cyclic extension"

```
[Diagram: Cyclic Prefix Creation]

Original OFDM symbol (N samples):
┌─────────────────────────────────────────────┐
│ s[0] s[1] ... s[N-Ncp-1] │ s[N-Ncp] ... s[N-1] │
└─────────────────────────────────────────────┘
                           └────────┬────────┘
                                    │ Copy this part
                                    ▼
Symbol with CP (N + Ncp samples):
┌───────────────────┬─────────────────────────────────────────────┐
│ s[N-Ncp] ... s[N-1] │ s[0] s[1] ... s[N-Ncp-1] │ s[N-Ncp] ... s[N-1] │
└───────────────────┴─────────────────────────────────────────────┘
        ↑                                            ↑
   Cyclic Prefix                              Same as CP
   (guard interval)
```

**Why CP Works:**

**ISI Elimination:** If CP length ≥ maximum channel delay spread (τmax), multipath components from the previous symbol fall entirely within the CP of the current symbol. The receiver discards the CP, eliminating ISI.

**Circular Convolution:** Linear convolution with the channel becomes circular convolution when CP is present. Circular convolution in time domain equals multiplication in frequency domain, enabling simple one-tap equalization per subcarrier.

**CP Length Selection:**
$T_{cp} \geq \tau_{max}$

Typical values: 1/4 to 1/8 of symbol duration. Longer CP provides more protection but reduces spectral efficiency (CP carries no new information).

**Spectral Efficiency Impact:**
$\eta = \frac{T_s}{T_s + T_{cp}} = \frac{1}{1 + T_{cp}/T_s}$

For Tcp/Ts = 1/4: η = 80% (20% overhead)

### 7.4 Direct Sequence Spread Spectrum (DSSS)

**Definition and Concept:**
DSSS is a spread spectrum technique where the narrowband data signal is multiplied by a high-rate pseudo-random noise (PN) code, spreading the signal energy across a much wider bandwidth. This provides interference resistance, multiple access capability, and security through low probability of intercept.

**Basic DSSS Operation:**

```
[Diagram: DSSS Transmitter]

Data Signal d(t)     ┌──────────┐
(Rate: Rb bps) ─────►│          │
  ±1 values          │    ⊗     │──────► Spread Signal s(t)
                     │(Multiply)│       (Rate: Rc = N·Rb)
PN Code c(t)         │          │        ±1 values
(Chip rate: Rc) ────►└──────────┘
  ±1 values

                     ┌──────────┐
Spread Signal ──────►│    ⊗     │──────► Modulated RF
                     │(Multiply)│
Carrier cos(2πfct)──►└──────────┘
```

**Mathematical Expressions:**

**Transmitted Signal:**
$s(t) = d(t) \cdot c(t) \cdot \cos(2\pi f_c t)$

Where:
- **d(t)** = Data signal (±1, rate Rb)
- **c(t)** = PN spreading code (±1, chip rate Rc)
- **fc** = Carrier frequency

**Spreading Factor (Processing Gain):**
$G_p = \frac{R_c}{R_b} = \frac{T_b}{T_c} = \frac{W_{spread}}{W_{data}} = N$

Where:
- **Rc** = Chip rate (chips per second)
- **Rb** = Data bit rate (bits per second)
- **Tb** = Bit duration
- **Tc** = Chip duration
- **N** = Number of chips per bit (spreading factor)

**In dB:**
$G_p(dB) = 10\log_{10}(N)$

**Example:** If Rb = 10 kbps and Rc = 1.28 Mcps, then Gp = 128 (21 dB processing gain).

**DSSS Receiver (Despreading Process):**

```
[Diagram: DSSS Receiver]

Received      ┌──────────┐   ┌──────────┐   ┌───────────┐   ┌──────────┐
Signal ──────►│ RF Front │──►│    ⊗     │──►│ Integrate │──►│ Decision │──► Data
r(t)          │   End    │   │(Multiply)│   │  & Dump   │   │  Device  │    Out
              └──────────┘   └────┬─────┘   │   (Tb)    │   └──────────┘
                                  │         └───────────┘
                            ┌─────┴──────┐
                            │ Local PN   │ ← Must be synchronized
                            │ Generator  │   with transmitter PN
                            └────────────┘
```

**Despreading Mathematics:**

Received signal (ignoring noise): r(t) = d(t)·c(t)·cos(2πfct)

After mixing with local carrier: r'(t) = d(t)·c(t)

After multiplication with synchronized local PN code:
$r''(t) = d(t) \cdot c(t) \cdot c(t) = d(t) \cdot c^2(t) = d(t) \cdot 1 = d(t)$

Since c(t) = ±1, we have c²(t) = 1, perfectly recovering the original data!

**Integration over bit period Tb:**
$y = \int_0^{T_b} d(t) \cdot dt = \pm T_b$

The integrator (matched filter) maximizes SNR for detection.

**Key Properties and Advantages of DSSS:**

**1. Interference Rejection (Anti-Jam):**
Narrowband interference j(t) at receiver becomes:
$j(t) \cdot c(t) = \text{spread interference}$

After despreading, interference power is spread across bandwidth Wss while signal is concentrated in bandwidth Wb:
$SNR_{improvement} = \frac{W_{ss}}{W_b} = G_p$

A jammer must transmit Gp times more power to have the same effect as jamming a narrowband system.

**2. Low Probability of Intercept (LPI):**
Transmitted power spectral density is very low (spread across wide bandwidth):
$PSD = \frac{P_t}{W_{ss}} = \frac{P_t}{G_p \cdot W_b}$

Signal appears noise-like to unintended receivers without the correct PN code.

**3. Low Probability of Detection (LPD):**
Signal is buried below noise floor, making it difficult to even detect that transmission is occurring.

**4. Code Division Multiple Access (CDMA):**
Multiple users can share the same frequency band simultaneously using different PN codes:
$s_{total}(t) = \sum_{i=1}^{K} d_i(t) \cdot c_i(t) \cdot \cos(2\pi f_c t)$

Each receiver despreads only its intended signal; other users appear as noise. System capacity is interference-limited:
$K_{max} \approx \frac{G_p}{E_b/N_0 \cdot (1 + f)}$

Where f = other-cell interference factor (typically 0.5-0.6).

**5. Multipath Resolution:**
Multipath components separated by more than Tc can be resolved. The RAKE receiver exploits this for diversity:
$\text{Resolvable paths if: } \Delta\tau > T_c = \frac{1}{R_c}$

**PN Code Properties (Requirements for Good Codes):**

**Autocorrelation:** Sharp peak at zero lag, near-zero elsewhere (good for synchronization):
$R_{cc}(\tau) = \begin{cases} N & \tau = 0 \\ -1/N & \tau \neq 0 \end{cases}$

**Cross-correlation:** Low between different codes (minimizes multiple access interference):
$R_{c_i c_j}(\tau) \approx 0 \text{ for } i \neq j$

**Balance:** Approximately equal number of +1s and -1s.

**Run-length:** Statistical properties of consecutive same symbols should match random sequence.

**Common PN Code Families:**
- **M-sequences (Maximal length):** Length 2^n - 1, excellent autocorrelation
- **Gold codes:** Good cross-correlation, widely used in GPS and CDMA
- **Kasami codes:** Very low cross-correlation
- **Walsh-Hadamard codes:** Perfect orthogonality (used in synchronous CDMA downlink)

**DSSS vs. OFDM Comparison:**

| Aspect | DSSS | OFDM |
|--------|------|------|
| Bandwidth efficiency | Lower (spreading) | Higher |
| Multipath handling | RAKE receiver | Cyclic prefix |
| Multiple access | CDMA (codes) | OFDMA (subcarriers) |
| Interference resistance | High (Gp) | Lower |
| Complexity | Moderate | Higher (FFT) |
| Near-far problem | Significant | Less significant |
| Peak-to-average power | Low | High (PAPR issue) |

---

## 8. POISSON TRAFFIC MODEL

### Introduction and Importance
The Poisson traffic model is the fundamental mathematical framework for analyzing telephone traffic and dimensioning telecommunications networks. Named after French mathematician Siméon Denis Poisson, this model describes the random arrival of calls in a system where many independent users each have a small probability of making a call at any given moment. Understanding this model is essential for network planning, capacity dimensioning, and quality of service analysis.

The Poisson model's elegance lies in its simplicity and mathematical tractability while providing surprisingly accurate predictions for real telephone networks. It forms the basis of Erlang's queuing theory formulas used worldwide for network dimensioning.

### Poisson Process - Fundamental Characteristics

A Poisson process is defined by three key properties:

**1. Stationarity (Homogeneity):**
The average arrival rate λ (calls per unit time) is constant over the observation period. The probability of an arrival in any small interval depends only on the interval length, not on when the interval occurs. Note: Real traffic varies over time, but is approximated as stationary over short periods (e.g., busy hour).

**2. Independence:**
Arrivals in non-overlapping time intervals are statistically independent. Whether a call arrived in the last minute has no effect on whether a call will arrive in the next minute. This models the realistic assumption that different users make calls independently.

**3. Orderliness (No Simultaneous Events):**
The probability of more than one arrival in an infinitesimally small interval dt approaches zero faster than dt itself:
$P(\text{2+ arrivals in } dt) = o(dt) \approx 0$

In other words, in a very small time interval, either zero or one arrival occurs, never two or more simultaneously.

### Poisson Distribution - Mathematical Derivation

From the above properties, we can derive that the number of arrivals in time interval T follows a Poisson distribution.

**Derivation Sketch:**
Divide interval T into n small subintervals of length T/n. As n→∞, each subinterval has probability λT/n of containing an arrival and probability (1 - λT/n) of being empty. The number of arrivals follows a binomial distribution with parameters n and p = λT/n. Taking the limit as n→∞ yields the Poisson distribution.

**Poisson Probability Mass Function:**

$P(k \text{ arrivals in time } T) = P(N(T) = k) = \frac{(\lambda T)^k \cdot e^{-\lambda T}}{k!}$

**Where:**
- **λ** = Average arrival rate (calls per unit time)
- **T** = Time interval of observation
- **k** = Number of arrivals (k = 0, 1, 2, 3, ...)
- **λT** = Expected number of arrivals in interval T

**Statistical Properties:**

**Mean (Expected Value):**
$E[N(T)] = \lambda T$

**Variance:**
$Var[N(T)] = \lambda T$

**Key Property:** For a Poisson distribution, mean equals variance! This property can be used to test whether real data follows a Poisson distribution.

**Standard Deviation:**
$\sigma = \sqrt{\lambda T}$

**Example Calculation:**
A cell receives an average of λ = 60 calls per hour. What is the probability of exactly 5 calls in a 5-minute period?

Solution:
T = 5/60 = 1/12 hour
λT = 60 × (1/12) = 5 (expected calls in 5 minutes)
$P(k=5) = \frac{5^5 \cdot e^{-5}}{5!} = \frac{3125 \times 0.00674}{120} = 0.1755 = 17.55\%$

### Inter-arrival Time Distribution

The time between consecutive arrivals (inter-arrival time) in a Poisson process follows an **exponential distribution**.

**Probability Density Function (PDF):**
$f(t) = \lambda e^{-\lambda t}, \quad t \geq 0$

**Cumulative Distribution Function (CDF):**
$F(t) = P(T \leq t) = 1 - e^{-\lambda t}$

**Survival Function (Probability of waiting longer than t):**
$P(T > t) = e^{-\lambda t}$

**Mean Inter-arrival Time:**
$E[T] = \frac{1}{\lambda}$

**Variance of Inter-arrival Time:**
$Var[T] = \frac{1}{\lambda^2}$

```
[Diagram: Exponential Distribution of Inter-arrival Times]

f(t) │
     │╲
  λ  │ ╲
     │  ╲
     │   ╲
     │    ╲
     │     ╲__
     │        ╲___
     │            ╲_____
     │                  ╲________
     └─────────────────────────────────► t
     0    1/λ    2/λ    3/λ    4/λ
          ↑
     Mean inter-arrival time
```

### Memoryless Property

The exponential distribution has the unique **memoryless property**:
$P(T > t + s \,|\, T > t) = P(T > s)$

**Interpretation:** Given that no arrival has occurred in the last t time units, the probability of waiting at least s more time units is the same as the unconditional probability of waiting s time units from the start.

**Proof:**
$P(T > t + s \,|\, T > t) = \frac{P(T > t + s)}{P(T > t)} = \frac{e^{-\lambda(t+s)}}{e^{-\lambda t}} = e^{-\lambda s} = P(T > s)$

**Practical Implication:** If you've been waiting 10 minutes for a bus that arrives according to a Poisson process, your expected additional wait time is the same as if you just arrived at the stop. The past doesn't help predict the future—this is why the Poisson process models "random" arrivals.

### Application to Teletraffic Engineering

**Traffic Intensity (Offered Load):**
$A = \lambda \times h \text{ (Erlangs)}$

Where:
- λ = Call arrival rate (calls per unit time)
- h = Average call holding time (same time unit)
- A = Offered traffic intensity

**Relationship with Service Rate:**
If μ = 1/h is the service rate (call completion rate), then:
$A = \frac{\lambda}{\mu}$

**Example:**
Busy hour statistics: λ = 120 calls/hour, average duration h = 3 minutes = 0.05 hours
$A = 120 \times 0.05 = 6 \text{ Erlangs}$

This means on average, 6 channels are simultaneously occupied.

### Erlang B Formula (Based on Poisson Arrivals)

For a system with N channels and offered traffic A Erlangs, assuming Poisson arrivals, exponential holding times, and blocked calls cleared (lost):

$P_B = \frac{A^N/N!}{\sum_{k=0}^{N} A^k/k!}$

This gives the probability that all N channels are busy when a new call arrives (blocking probability).

### Validity and Limitations of Poisson Model

**When Poisson Model is Appropriate:**
- Large population of independent users
- Each user generates calls infrequently (small individual probability)
- No correlation between different users' behaviors
- Traditional voice telephony with human-generated traffic
- System not in overload (arrivals independent of system state)

**When Poisson Model May Fail:**
- Bursty data traffic (web browsing, video streaming) - better modeled by self-similar or Pareto distributions
- Overload conditions where users retry blocked calls - creates correlated arrivals
- Small user populations where individual behavior matters
- Machine-generated traffic with synchronized patterns (IoT devices reporting simultaneously)
- Callback systems where blocked calls create future arrivals

**Testing for Poisson Behavior:**
1. Check if mean ≈ variance (Poisson property)
2. Chi-square goodness-of-fit test
3. Plot inter-arrival time histogram against exponential distribution

### Extensions of Poisson Model

**Non-homogeneous Poisson Process:**
Arrival rate λ(t) varies with time. Used to model daily traffic variations:
$P(k \text{ arrivals in } [0,T]) = \frac{(\Lambda(T))^k e^{-\Lambda(T)}}{k!}$
where $\Lambda(T) = \int_0^T \lambda(t)dt$

**Compound Poisson Process:**
Each arrival brings a random number of "items" (e.g., batch arrivals).

**Marked Poisson Process:**
Each arrival has associated random "marks" (e.g., call duration, call type).

---

## 9. TRAFFIC INTENSITY, GoS, AND TRUNKING EFFICIENCY

### Fundamental Definitions and Concepts

**Traffic Intensity (A):**
Traffic intensity, measured in Erlangs, represents the average number of simultaneous calls or occupied channels. One Erlang equals one circuit continuously occupied for the duration of the measurement period (typically one hour).

$A = \lambda \times h = \frac{\text{Total holding time}}{\text{Observation period}} = \frac{\sum_{i=1}^{n} h_i}{T}$

**Where:**
- λ = Call arrival rate (calls per hour)
- h = Mean holding time (hours)
- hi = Duration of i-th call
- T = Observation period

**Example Interpretations:**
- A = 1 Erlang: On average, 1 channel is always busy
- A = 10 Erlangs: On average, 10 simultaneous calls
- A = 0.5 Erlangs: A channel is busy 50% of the time

**Offered Traffic vs. Carried Traffic:**
- **Offered Traffic (A):** Total traffic demand from users (includes blocked calls)
- **Carried Traffic (C):** Traffic actually served by the network
- **Relationship:** C = A × (1 - PB), where PB is blocking probability

**Grade of Service (GoS):**
GoS is a measure of service quality, typically defined as the probability that a call attempt is blocked (not served) during the busy hour.

$GoS = P_B = P(\text{all channels busy})$

**Typical GoS Targets:**
- Voice networks: 0.01 - 0.02 (1-2% blocking)
- Emergency services: 0.001 (0.1% blocking)
- Premium services: 0.005 (0.5% blocking)

**Trunking Efficiency (η):**
Trunking efficiency measures how effectively channels are utilized:

$\eta = \frac{\text{Carried Traffic}}{\text{Number of Channels}} = \frac{A(1-P_B)}{N} = \frac{C}{N}$

Maximum possible efficiency is 1.0 (100%) when all channels are always busy, but this would mean 100% blocking of new calls.

### Erlang B Formula - The Foundation

The Erlang B formula calculates blocking probability for a system with N channels, offered traffic A Erlangs, assuming Poisson arrivals, exponential holding times, and blocked calls cleared:

$P_B = B(N, A) = \frac{A^N/N!}{\sum_{k=0}^{N} A^k/k!}$

**Recursive Form (easier to compute):**
$B(N, A) = \frac{A \cdot B(N-1, A)}{N + A \cdot B(N-1, A)}, \quad B(0, A) = 1$

### Relationship Between GoS, Channels, and Trunking Efficiency

**Key Insight: Trunking Gain (Statistical Multiplexing)**

When channels are shared among many users (trunked), efficiency improves dramatically compared to dedicated channels. This is because:
- Not all users need service simultaneously
- Statistical smoothing occurs with larger pools
- Resource utilization improves with scale

```
[Diagram: Trunking Efficiency vs Number of Channels]

Efficiency │                                    
(%)        │                              ╭────── 2% GoS
    100 ───│─────────────────────────────╱──────
           │                           ╱
     80 ───│─────────────────────────╱──────────
           │                       ╱
     60 ───│─────────────────────╱──────────────
           │                   ╱ ╱
     40 ───│─────────────────╱─╱────────────────
           │               ╱ ╱
     20 ───│─────────────╱─╱────────────────────
           │           ╱ ╱ ← 5% GoS
      0 ───│─────────╱─╱────────────────────────
           └───────────────────────────────────────►
               1    10    20    50    100   200
                    Number of Channels (N)
```

**Numerical Demonstration of Trunking Gain:**

For 2% GoS (PB = 0.02):

| Channels (N) | Max Traffic (A) | Efficiency (η = A/N) | Traffic per Channel |
|--------------|-----------------|----------------------|---------------------|
| 1 | 0.02 E | 2% | 0.020 E |
| 4 | 1.09 E | 27% | 0.273 E |
| 10 | 5.08 E | 51% | 0.508 E |
| 20 | 13.18 E | 66% | 0.659 E |
| 50 | 40.26 E | 81% | 0.805 E |
| 100 | 87.97 E | 88% | 0.880 E |
| 200 | 186.4 E | 93% | 0.932 E |

**Observation:** A single channel can only carry 0.02 Erlangs at 2% blocking, but 100 shared channels can carry 88 Erlangs—4,400 times more efficient per channel!

### How GoS Influences Trunking Efficiency

**Stricter GoS (lower blocking) → Lower efficiency:**

For N = 20 channels:

| GoS Target | Blocking (PB) | Traffic Carried (A) | Efficiency (η) |
|------------|---------------|---------------------|----------------|
| Relaxed | 5% | 15.25 E | 76% |
| Standard | 2% | 13.18 E | 66% |
| Strict | 1% | 12.03 E | 60% |
| Very Strict | 0.1% | 9.41 E | 47% |

**Trade-off:** To guarantee better service (lower blocking), we must either add more channels or accept lower utilization of existing channels.

### How Channel Availability Influences Efficiency

**More channels serving common pool → Higher efficiency:**

This is because large systems benefit from statistical multiplexing—peaks and valleys of individual users' demands average out. The law of large numbers applies: variance decreases relative to mean.

**Mathematical Relationship:**
For large N with fixed GoS, efficiency approaches:
$\eta \approx 1 - \sqrt{\frac{2P_B}{\pi N}} \text{ (asymptotic approximation)}$

This shows efficiency approaches 100% as N → ∞, but the rate of improvement decreases.

**Marginal Gain Decreases:**
Going from 10 to 20 channels: efficiency improves from 51% to 66% (+15%)
Going from 100 to 110 channels: efficiency improves from 88% to 89% (+1%)

### Design Trade-offs in Cellular Systems

**Cell Size vs. Efficiency:**
- Larger cells have more channels → higher efficiency
- But larger cells serve more area → may have capacity problems
- Solution: Match cell size to traffic density

**Frequency Reuse vs. Efficiency:**
- Smaller reuse factor (N) → more channels per cell → higher efficiency
- But smaller N → more interference → need better power control
- CDMA achieves N=1 (universal reuse) through power control and interference averaging

**Sectoring Trade-off:**
- 3-sector cell: 3× more channel groups, but each sector serves 1/3 area
- Improves interference but may reduce trunking efficiency if sectors have few channels
- Most beneficial for large cells with many channels

**Guard Channels for Handover:**
- Reserving channels for handovers improves handover success rate
- But reduces channels available for new calls → increases new call blocking
- Typical: Reserve 1-2 channels per cell for handovers

### Erlang B Table (Extended Reference)

| N | 1% GoS | 2% GoS | 5% GoS | 10% GoS |
|---|--------|--------|--------|---------|
| 1 | 0.010 | 0.020 | 0.053 | 0.111 |
| 2 | 0.153 | 0.223 | 0.381 | 0.595 |
| 5 | 1.361 | 1.657 | 2.218 | 2.881 |
| 10 | 4.461 | 5.084 | 6.216 | 7.511 |
| 15 | 8.108 | 9.010 | 10.63 | 12.48 |
| 20 | 12.03 | 13.18 | 15.25 | 17.61 |
| 30 | 20.34 | 21.93 | 24.80 | 28.11 |
| 40 | 29.01 | 31.00 | 34.60 | 38.82 |
| 50 | 37.90 | 40.26 | 44.53 | 49.64 |
| 70 | 56.10 | 59.13 | 64.59 | 71.46 |
| 100 | 84.06 | 87.97 | 95.24 | 104.5 |

---

## 10. PROPAGATION DELAY

### Definition and Fundamental Concept
**Propagation delay** is the time required for an electromagnetic signal to travel from the transmitter to the receiver through a medium. This is a fundamental physical constraint that cannot be reduced below the speed of light limit. Understanding propagation delay is crucial for protocol design, synchronization systems, and determining maximum communication distances.

$t_{prop} = \frac{d}{v}$

**Where:**
- **tprop** = Propagation delay (seconds)
- **d** = Distance between transmitter and receiver (meters)
- **v** = Propagation velocity of the signal in the medium (m/s)

### Propagation Velocity in Different Media

The propagation velocity depends on the medium through which the signal travels:

| Medium | Velocity | Fraction of c | Delay per km |
|--------|----------|---------------|--------------|
| Free space / Air | 3 × 10⁸ m/s | 1.0 | 3.33 μs |
| Coaxial cable | ~2 × 10⁸ m/s | 0.67 | 5.0 μs |
| Optical fiber | ~2 × 10⁸ m/s | 0.67 | 5.0 μs |
| Twisted pair | ~2 × 10⁸ m/s | 0.67 | 5.0 μs |
| Waveguide | ~2.5 × 10⁸ m/s | 0.83 | 4.0 μs |

In guided media (cables, fibers), the signal travels slower than in free space due to the dielectric constant of the material:
$v = \frac{c}{\sqrt{\epsilon_r}} = \frac{c}{n}$

Where εr is the relative permittivity and n is the refractive index.

### Significance in Wireless Communications

**1. Timing Advance in GSM and LTE**

In TDMA systems like GSM, mobiles share a frequency by transmitting in different time slots. For the base station to receive non-overlapping bursts, mobiles must compensate for propagation delay by transmitting earlier:

```
[Diagram: Timing Advance Concept]

Without Timing Advance:
BS View:  │ Slot 0 │ Slot 1 │ Slot 2 │ Slot 3 │
          │  MS1   │overlap!│  MS2   │  MS3   │
                    ↑
          Far MS1's signal arrives late, overlapping Slot 1

With Timing Advance:
MS1 transmits early by TA = 2d/c
BS View:  │ Slot 0 │ Slot 1 │ Slot 2 │ Slot 3 │
          │  MS1   │  MS2   │  MS3   │  (ok)  │
          
All bursts arrive in correct slots
```

**Timing Advance Calculation:**
$TA = \frac{2d}{c} \times \text{symbol rate}$

The factor of 2 accounts for the round-trip delay used in ranging.

**GSM Timing Advance:**
- TA range: 0-63 (6 bits)
- Each TA unit ≈ 3.69 μs (one bit period)
- Maximum distance: 63 × 3.69 μs × c/2 ≈ 35 km
- This limits GSM cell radius to approximately 35 km

**LTE Timing Advance:**
- TA range: 0-1282 (11 bits for initial, extended for larger cells)
- Maximum distance: ~100 km with extended TA

**2. Round-Trip Time (RTT) and Its Applications**

$RTT = 2 \times t_{prop} + t_{processing}$

**Distance Estimation (Ranging):**
$d = \frac{RTT \times c}{2}$

Used in radar, GPS, cellular positioning, and network latency estimation.

**Impact on Protocols:**
- TCP congestion control uses RTT for timeout calculation
- ARQ protocols wait RTT before retransmitting
- Higher RTT → lower throughput for window-based protocols

**3. Guard Intervals in TDD Systems**

In Time Division Duplex (TDD), the same frequency is used for uplink and downlink in alternating time periods. Guard time between UL and DL must accommodate the maximum propagation delay in the cell:

```
[Diagram: TDD Guard Time]

Time →  │ Downlink │ Guard │ Uplink │ Guard │ Downlink │
        │   Slot   │ Time  │  Slot  │ Time  │   Slot   │
                     ↑
              Must be ≥ 2×(d_max/c)
              to prevent UL/DL overlap
```

**Minimum Guard Time:**
$T_{guard} \geq \frac{2 \times d_{max}}{c}$

For a 10 km cell: Tguard ≥ 2 × 10000 / (3×10⁸) = 67 μs

**4. Satellite Communications**

Propagation delay is most significant for satellite systems:

**Low Earth Orbit (LEO) Satellites (500-2000 km):**
- One-way delay: 2-7 ms
- RTT: 4-14 ms
- Acceptable for interactive applications

**Medium Earth Orbit (MEO) Satellites (8,000-20,000 km):**
- One-way delay: 27-67 ms
- RTT: 54-134 ms
- GPS satellites operate in MEO

**Geostationary Orbit (GEO) Satellites (35,786 km):**
$t_{prop} = \frac{35,786 \times 10^3 \text{ m}}{3 \times 10^8 \text{ m/s}} \approx 119 \text{ ms (one-way)}$
$RTT \approx 240 \text{ ms (Earth-satellite-Earth)}$
$\text{End-to-end delay} \approx 480-600 \text{ ms (including processing)}$

This significant delay is noticeable in voice calls and problematic for real-time applications. GEO links require special TCP optimizations.

**5. Maximum Cell Size Constraints**

Propagation delay limits the maximum cell size in cellular systems. Beyond a certain distance, timing synchronization cannot be maintained within protocol constraints.

**GSM Example:**
- Maximum TA value: 63
- Bit period: 3.69 μs
- Maximum measurable round-trip delay: 63 × 3.69 = 232.5 μs
- Maximum distance: 232.5 × 10⁻⁶ × 3 × 10⁸ / 2 ≈ 35 km

**Extended Range Solutions:**
- Extended TA modes in later releases
- Special extended-range cell configurations
- Repeaters to extend coverage without increasing cell radius

### Propagation Delay vs. Other Network Delays

Total end-to-end delay in a communication system has multiple components:

**Transmission Delay (Dtrans):**
Time to put all bits of a packet onto the medium:
$D_{trans} = \frac{\text{Packet size (bits)}}{\text{Data rate (bps)}}$

**Propagation Delay (Dprop):**
Time for signal to travel through medium:
$D_{prop} = \frac{\text{Distance}}{\text{Propagation velocity}}$

**Processing Delay (Dproc):**
Time for node to process packet (routing decisions, error checking):
- Typically microseconds to milliseconds
- Depends on processor speed and protocol complexity

**Queuing Delay (Dqueue):**
Time spent waiting in buffers:
- Highly variable, depends on traffic load
- Can dominate total delay during congestion

**Total End-to-End Delay:**
$D_{total} = \sum_{i=1}^{n} (D_{trans,i} + D_{prop,i} + D_{proc,i} + D_{queue,i})$

Where n is the number of links in the path.

**Comparison for Different Scenarios:**

| Scenario | Dominant Delay Component |
|----------|--------------------------|
| Satellite link | Propagation delay |
| High-speed LAN | Transmission delay |
| Congested router | Queuing delay |
| Wireless last hop | Processing + Propagation |
| Intercontinental fiber | Propagation delay |

### Numerical Examples

**Example 1:** Calculate propagation delay for a 15 km cellular link.
$t_{prop} = \frac{15 \times 10^3}{3 \times 10^8} = 50 \text{ μs}$

**Example 2:** A mobile is 8 km from the base station. What timing advance is needed in GSM?
$RTT = \frac{2 \times 8000}{3 \times 10^8} = 53.3 \text{ μs}$
$TA = \frac{53.3}{3.69} \approx 14.4 \rightarrow TA = 15$

**Example 3:** Compare delay components for sending a 1500-byte packet over a 100 Mbps link spanning 1000 km of fiber.
- Transmission delay: (1500 × 8) / (100 × 10⁶) = 120 μs
- Propagation delay: (1000 × 10³) / (2 × 10⁸) = 5000 μs = 5 ms
- Propagation delay dominates!

---

## 11. CRITICAL FREQUENCY

### Definition and Physical Basis
**Critical frequency (fc)** is the highest frequency of a radio wave that will be reflected back to Earth when transmitted vertically (straight up) at the ionosphere. Frequencies above the critical frequency pass through the ionosphere into space rather than being reflected. This parameter is fundamental to HF (High Frequency) radio communication, which relies on ionospheric reflection for long-distance transmission beyond the horizon.

The ionosphere is a region of Earth's upper atmosphere (approximately 60-1000 km altitude) where solar radiation ionizes gas molecules, creating free electrons and ions. This ionized layer acts as a reflector for radio waves below certain frequencies, enabling over-the-horizon communication.

### Physical Mechanism of Ionospheric Reflection

When a radio wave enters the ionosphere, it encounters free electrons. These electrons oscillate in response to the wave's electric field, creating a secondary wave that combines with the original. The effective result is that the wave is bent (refracted) back toward Earth—but only if the frequency is below a critical threshold.

```
[Diagram: Ionospheric Reflection vs Penetration]

                         Space (f > fc passes through)
                              ↑
    ════════════════════════════════════════════════
                     IONOSPHERE
              Electron density increases with height
              Maximum density at peak (N_max)
    ════════════════════════════════════════════════
           ↗          ↑            ↖
         ╱            │              ╲
        ╱    f < fc   │   f = fc      ╲  f < fc
       ╱   (reflects) │  (grazing)     ╲ (reflects)
      ╱               │                 ╲
    ─────────────────────────────────────────────────
         Transmitter              Receiver
                    EARTH
```

**Why Reflection Occurs:**
The refractive index n of the ionosphere depends on frequency and electron density:
$n = \sqrt{1 - \frac{f_p^2}{f^2}} = \sqrt{1 - \frac{81N}{f^2}}$

Where:
- fp = plasma frequency (Hz)
- N = electron density (electrons/m³)
- f = wave frequency (Hz)

When n approaches zero, total internal reflection occurs. This happens when f ≤ fp = 9√N.

### Mathematical Expression for Critical Frequency

The critical frequency is the plasma frequency at the layer's maximum electron density:

$f_c = 9\sqrt{N_{max}} \text{ (Hz, when N in electrons/m³)}$

**More Complete Expression:**
$f_c = \frac{1}{2\pi}\sqrt{\frac{N_{max} \cdot e^2}{\epsilon_0 \cdot m_e}}$

**Where:**
- **Nmax** = Maximum electron density in the ionospheric layer (electrons/m³)
- **e** = Electron charge (1.6 × 10⁻¹⁹ C)
- **me** = Electron mass (9.1 × 10⁻³¹ kg)
- **ε₀** = Permittivity of free space (8.85 × 10⁻¹² F/m)

**Simplified Formula (commonly used):**
$f_c = 9\sqrt{N_{max}} \text{ Hz} \quad \text{or} \quad f_c = 9 \times 10^{-3}\sqrt{N_{max}} \text{ MHz}$

**Example:** If Nmax = 10¹² electrons/m³:
$f_c = 9\sqrt{10^{12}} = 9 \times 10^6 \text{ Hz} = 9 \text{ MHz}$

### Ionospheric Layers and Their Critical Frequencies

The ionosphere has several distinct layers, each with different characteristics:

```
[Diagram: Ionospheric Layer Structure]

Height (km)
    │
 400├────────────────────────────────────────
    │              F2 Layer
    │     (Main reflection layer, highest fc)
 250├────────────────────────────────────────
    │              F1 Layer
    │        (Present during day only)
 150├────────────────────────────────────────
    │              E Layer
    │     (Sporadic E can cause unusual propagation)
 100├────────────────────────────────────────
    │              D Layer
    │     (Absorbs rather than reflects)
  60├────────────────────────────────────────
    │
    │            ATMOSPHERE
    └────────────────────────────────────────
```

**Layer Characteristics:**

| Layer | Height (km) | Critical Frequency | Characteristics |
|-------|-------------|-------------------|-----------------|
| D Layer | 60-90 | 0.1-0.5 MHz | Absorbs MF/HF during day; disappears at night |
| E Layer | 100-120 | 1-4 MHz | Moderate ionization; supports regional HF |
| F1 Layer | 150-200 | 4-6 MHz | Present only during day; merges with F2 at night |
| F2 Layer | 250-400 | 5-15 MHz | Highest electron density; main long-distance layer |

### Factors Affecting Critical Frequency

**1. Time of Day:**
- Daytime: Solar radiation maintains ionization → higher fc
- Nighttime: No solar input → recombination reduces electrons → lower fc
- F2 layer fc can drop from 12 MHz (day) to 4 MHz (night)

**2. Season:**
- Summer: Longer daylight → higher average ionization
- Winter: Lower fc, but F2 layer can have anomalous behavior

**3. Solar Activity (11-Year Cycle):**
- Solar maximum: Intense radiation → high electron density → fc up to 15 MHz
- Solar minimum: Reduced radiation → fc may drop to 3-5 MHz

**4. Geographic Location:**
- Equatorial regions: Higher fc due to stronger solar radiation
- Polar regions: Aurora affects ionization; irregular propagation

**5. Geomagnetic Activity:**
- Solar storms can enhance or disturb ionosphere
- Sudden Ionospheric Disturbances (SIDs) can black out HF

### Maximum Usable Frequency (MUF)

For oblique incidence (waves not transmitted straight up), reflection can occur at higher frequencies. The Maximum Usable Frequency is:

$MUF = \frac{f_c}{\cos\theta} = f_c \cdot \sec\theta$

**Where θ is the angle of incidence (from vertical).**

This relationship is called the **Secant Law** or **MUF equation**.

```
[Diagram: Oblique Incidence and MUF]

                    Ionosphere
    ══════════════════════════════════════════
              ↑          ╲
              │           ╲
              │ θ          ╲ (oblique path)
              │             ╲
    ──────────┴──────────────╲────────────────
           Tx                  Rx
    
    Vertical incidence: reflects if f < fc
    Oblique incidence: reflects if f < fc·sec(θ)
    
    Greater angle → higher MUF → longer skip distance
```

**MUF Calculation Example:**
If fc = 8 MHz and incidence angle θ = 75°:
$MUF = 8 \times \sec(75°) = 8 \times 3.86 = 30.9 \text{ MHz}$

**Skip Distance:**
The skip distance is the minimum distance at which sky-wave propagation can be received. Inside this distance, only ground wave reaches (if at all):
$d_{skip} = 2h\tan\theta$

Where h is the virtual height of the ionospheric layer.

### Lowest Usable Frequency (LUF)

The LUF is the lowest frequency that provides usable signal strength. Below LUF, absorption in the D layer is too severe:

**LUF Characteristics:**
- Typically 2-6 MHz during day
- Lower at night (D layer disappears)
- Depends on transmitter power and required SNR

### Optimum Working Frequency (OWF)

The OWF provides a margin below MUF to account for ionospheric variability:

$OWF = 0.85 \times MUF$

Using OWF instead of MUF ensures reliable communication despite short-term ionospheric fluctuations.

**Frequency Selection Window:**
$LUF < f_{operating} < OWF < MUF$

```
[Diagram: Frequency Selection]

Frequency │                          │
          │ ─────────────────────────│── MUF (15 MHz)
          │                          │
          │ ═════════════════════════│══ OWF (12.75 MHz)
          │    ↑                     │
          │    │ Operating Window    │
          │    ↓                     │
          │ ═════════════════════════│══ LUF (4 MHz)
          │                          │
     0 ───┴──────────────────────────┴────
              Usable frequency range
```

### Applications and Significance

**1. HF Radio Communication (3-30 MHz):**
Long-distance communication without satellites, used by military, maritime, aviation, amateur radio, and emergency services.

**2. Over-the-Horizon Radar (OTHR):**
Detects aircraft and ships beyond line-of-sight using ionospheric reflection.

**3. Frequency Planning:**
Broadcasters and communication services must plan frequencies based on predicted fc and MUF values. Ionospheric prediction services provide forecasts.

**4. Satellite Communication:**
Frequencies above MUF are used for satellite links to ensure signals pass through the ionosphere without reflection.

**5. GPS and Navigation:**
Ionospheric delay affects GPS accuracy; dual-frequency receivers correct for this effect.

---

## 12. LINE-OF-SIGHT (LOS) FORMULA

### Definition and Concept
Line-of-sight propagation occurs when there is a clear, unobstructed direct path between transmitter and receiver. For terrestrial wireless links, the maximum LOS distance is fundamentally limited by Earth's curvature, which causes the surface to drop away below a straight line between elevated antennas. The LOS formula calculates this maximum distance based on antenna heights.

Understanding LOS distance is critical for designing microwave links, cellular networks, broadcast systems, and any wireless system operating above approximately 30 MHz where ionospheric reflection doesn't occur.

### Geometric Derivation

Consider an antenna at height h above Earth's surface. The horizon distance d is where a straight line from the antenna is tangent to Earth's surface:

```
[Diagram: LOS Geometry Derivation]

                         Antenna
                           │
                           │ h (height)
                          ╱│
                        ╱  │
                      ╱    │
            d       ╱      │
        (LOS)    ╱        │
              ╱           │
            ╱──────────────┤ Tangent point (horizon)
          ╱                 ╲
        ╱                    ╲
       │         R            ╲  R (Earth's radius)
       │                       │
       └───────────────────────┘
              Earth's Center
```

Using the Pythagorean theorem:
$(R + h)^2 = R^2 + d^2$
$R^2 + 2Rh + h^2 = R^2 + d^2$
$d^2 = 2Rh + h^2$

Since h << R (antenna height is much smaller than Earth's radius):
$d^2 \approx 2Rh$
$d = \sqrt{2Rh}$

### Basic LOS Distance Formula

For two antennas at heights h₁ and h₂:

$d_{LOS} = \sqrt{2Rh_1} + \sqrt{2Rh_2}$

**Where:**
- **dLOS** = Maximum line-of-sight distance (meters)
- **R** = Earth's radius (6.37 × 10⁶ m or 6,370 km)
- **h₁** = Height of first antenna (meters)
- **h₂** = Height of second antenna (meters)

### Practical Formula in Kilometers

Substituting R = 6.37 × 10⁶ m:
$d_{LOS}(km) = \sqrt{2 \times 6.37 \times 10^6 \times h_1 \times 10^{-6}} + \sqrt{2 \times 6.37 \times 10^6 \times h_2 \times 10^{-6}}$

$\boxed{d_{LOS}(km) = 3.57(\sqrt{h_1} + \sqrt{h_2})}$

Where h₁ and h₂ are in **meters**.

**For single antenna to horizon (radio horizon):**
$d(km) = 3.57\sqrt{h}$

### Effective Earth Radius Model (4/3 Earth)

In reality, the atmosphere causes radio waves to bend slightly toward the Earth due to the refractive index gradient. This bending effectively extends the radio horizon beyond the geometric horizon.

This effect is modeled by using an **effective Earth radius** larger than the actual radius:

$R_{eff} = K \times R$

**Where K is the effective Earth radius factor:**
- K = 1: No atmospheric refraction (geometric)
- K = 4/3 ≈ 1.33: Standard atmosphere (most common)
- K > 4/3: Super-refraction (trapping, ducting)
- K < 1: Sub-refraction (can occur in certain weather)

**Standard Atmosphere LOS Formula (K = 4/3):**

$d_{LOS}(km) = 3.57\sqrt{K}(\sqrt{h_1} + \sqrt{h_2}) = 3.57\sqrt{4/3}(\sqrt{h_1} + \sqrt{h_2})$

$\boxed{d_{LOS}(km) = 4.12(\sqrt{h_1} + \sqrt{h_2})}$

This is the most commonly used formula for practical radio link design.

```
[Diagram: Effect of Atmospheric Refraction]

                    Geometric path (straight line)
                   ╱
                 ╱    ╭─── Actual radio path (curved)
               ╱   ╭──╯
             ╱  ╭──╯
           ╱╭───╯
         ╱──╯
    Tx ──────────────────────────────── Rx
       
    ═══════════════════════════════════════
                   EARTH
    
    Radio wave bends toward Earth due to atmosphere
    → Effectively extends horizon distance
    → Modeled as straight path over larger (4/3) Earth
```

### Fresnel Zone Clearance

For reliable LOS communication, it's not sufficient to just clear the geometric path. The **first Fresnel zone** should be substantially clear of obstructions to avoid diffraction losses.

**First Fresnel Zone Definition:**
The first Fresnel zone is an ellipsoid around the direct path where all points have path lengths within λ/2 of the direct path. Obstructions in this zone can cause significant signal attenuation.

**First Fresnel Zone Radius:**
At any point along the path, the radius of the first Fresnel zone is:

$r_1 = \sqrt{\frac{\lambda \cdot d_1 \cdot d_2}{d_1 + d_2}} = \sqrt{\frac{\lambda \cdot d_1 \cdot d_2}{D}}$

**Where:**
- λ = Wavelength (meters)
- d₁ = Distance from transmitter to the point
- d₂ = Distance from the point to receiver
- D = Total path length = d₁ + d₂

**Maximum Fresnel Radius (at midpoint):**
At the midpoint of the path (d₁ = d₂ = D/2):
$r_{1,max} = \frac{1}{2}\sqrt{\lambda D} = \sqrt{\frac{\lambda D}{4}}$

```
[Diagram: Fresnel Zone]

    Tx ═══════════════════════════════════════ Rx
           ╲                               ╱
            ╲                             ╱
             ╲       First Fresnel       ╱
              ╲         Zone            ╱
               ╲    (Ellipsoid)        ╱
                ╲                     ╱
                 ╲─────────r₁───────╱
                  ╲               ╱
                   ╲             ╱
                    ╲___________╱
                         ↑
                    Max radius at midpoint
```

**Clearance Requirements:**
- **100% clearance:** Ideal, no obstruction in first Fresnel zone
- **60% clearance:** Minimum acceptable; equivalent to knife-edge diffraction with ~0 dB loss
- **<60% clearance:** Significant diffraction loss expected

**Rule of Thumb for Tower Heights:**
To ensure adequate Fresnel zone clearance, add 60% of the maximum Fresnel radius to the geometric clearance requirement.

### Numerical Examples

**Example 1: Basic LOS Calculation**
Calculate the radio horizon for a cellular base station antenna at 50m height and a mobile at 1.5m height.

Using standard atmosphere formula:
$d_{LOS} = 4.12(\sqrt{50} + \sqrt{1.5}) = 4.12(7.07 + 1.22) = 4.12 \times 8.29 = 34.2 \text{ km}$

**Example 2: Microwave Link Design**
Design a 30 km microwave link at 6 GHz. What tower heights are needed?

λ = c/f = 3×10⁸/6×10⁹ = 0.05 m

For symmetric towers (h₁ = h₂ = h):
$30 = 4.12 \times 2\sqrt{h}$
$\sqrt{h} = 30/(4.12 \times 2) = 3.64$
$h = 13.25 \text{ m (geometric minimum)}$

Fresnel radius at midpoint:
$r_{1,max} = \sqrt{\frac{0.05 \times 30000}{4}} = \sqrt{375} = 19.4 \text{ m}$

For 60% clearance: need additional 0.6 × 19.4 = 11.6 m
**Recommended tower height: 13.25 + 11.6 ≈ 25 m each**

**Example 3: Radio Horizon Distance**
A ship has an antenna at 25m height. A coastal station has an antenna at 100m. What is the maximum communication distance?

$d_{LOS} = 4.12(\sqrt{100} + \sqrt{25}) = 4.12(10 + 5) = 61.8 \text{ km}$

### Factors Affecting LOS Propagation

**1. Atmospheric Refraction:**
The effective Earth radius factor K varies with weather:
- Standard atmosphere: K = 4/3
- Temperature inversion: K > 4/3 (extended range, possible ducting)
- Rain/fog: K may decrease (reduced range)

**2. Ducting:**
Under certain atmospheric conditions (temperature inversions), radio waves can become trapped in a "duct" and travel much farther than normal LOS distance. This can cause interference to distant systems.

**3. Terrain and Obstacles:**
Hills, buildings, and vegetation can obstruct the LOS path. Terrain profile analysis is essential for link design.

**4. Earth Bulge:**
For long paths, Earth's curvature creates a "bulge" that may obstruct the path:
$\text{Earth bulge (m)} = \frac{d_1 \cdot d_2}{2 \times K \times R}$

**5. Multipath Reflections:**
Reflections from ground or water surfaces can cause multipath fading. Antenna height diversity or space diversity can mitigate this.

**6. Atmospheric Absorption:**
At frequencies above 10 GHz, atmospheric gases (O₂, H₂O) cause absorption. Rain attenuation becomes significant above 10 GHz.

### Summary Table

| Parameter | Formula |
|-----------|---------|
| Geometric LOS | d = 3.57(√h₁ + √h₂) km |
| Standard atmosphere LOS (K=4/3) | d = 4.12(√h₁ + √h₂) km |
| Radio horizon (one antenna) | d = 4.12√h km |
| First Fresnel radius | r₁ = √(λd₁d₂/D) m |
| Maximum Fresnel radius | r₁max = √(λD/4) m |

---

## 13. FREQUENCY REUSE

### Concept and Importance
**Frequency reuse** is the foundational concept of cellular systems that enables serving a large number of users with a limited amount of spectrum. The key insight is that the same frequencies can be used simultaneously in different geographic areas (cells) that are sufficiently separated to avoid harmful interference. This spatial reuse multiplies the effective capacity of the available spectrum.

Without frequency reuse, a wireless system could only support as many simultaneous users as there are available channels. With frequency reuse, the same channels can serve users in many different locations, dramatically increasing system capacity. This concept transformed mobile communications from limited-capacity systems into the ubiquitous networks we have today.

### Cellular System Structure

The coverage area is divided into cells, each served by a base station. Cells are often modeled as hexagons for analysis, though actual cell shapes are irregular due to terrain and propagation effects.

```
[Diagram: Hexagonal Cell Layout with 7-Cell Reuse Pattern]

              ╱╲     ╱╲     ╱╲     ╱╲
             ╱ 2╲   ╱ 3╲   ╱ 2╲   ╱ 3╲
            ╱    ╲ ╱    ╲ ╱    ╲ ╱    ╲
           ╲  1  ╱╲  1  ╱╲  1  ╱╲  1  ╱
            ╲   ╱7 ╲   ╱7 ╲   ╱7 ╲   ╱
             ╲ ╱    ╲ ╱    ╲ ╱    ╲ ╱
             ╱╲  6  ╱╲  6  ╱╲  6  ╱╲
            ╱ 5╲   ╱ 5╲   ╱ 5╲   ╱ 5╲
           ╱    ╲ ╱    ╲ ╱    ╲ ╱    ╲
          ╲  4  ╱╲  4  ╱╲  4  ╱╲  4  ╱
           ╲   ╱  ╲   ╱  ╲   ╱  ╲   ╱
            ╲ ╱    ╲ ╱    ╲ ╱    ╲ ╱

    Cells with the same number use the same frequencies
    This is a 7-cell reuse pattern (N = 7)
    The pattern repeats (tessellates) across the coverage area
```

### Cluster and Cluster Size (N)

A **cluster** is a group of N cells that together use the complete set of available frequencies. The cluster pattern repeats across the coverage area.

**Valid Cluster Sizes for Hexagonal Geometry:**
For seamless tessellation with hexagonal cells, the cluster size must satisfy:

$N = i^2 + ij + j^2$

Where i and j are non-negative integers (not both zero).

**Valid Values:**
| i | j | N = i² + ij + j² |
|---|---|------------------|
| 1 | 0 | 1 |
| 1 | 1 | 3 |
| 2 | 0 | 4 |
| 2 | 1 | 7 |
| 3 | 0 | 9 |
| 2 | 2 | 12 |
| 3 | 1 | 13 |
| 4 | 0 | 16 |
| 3 | 2 | 19 |
| 4 | 1 | 21 |

**Common cluster sizes:** N = 3, 4, 7, 12 for different systems.

### Frequency Reuse Factor

The frequency reuse factor indicates what fraction of total frequencies is available in each cell:

$\text{Frequency Reuse Factor} = \frac{1}{N}$

**Impact on Capacity:**
- Smaller N → more frequencies per cell → higher capacity per cell
- Smaller N → closer co-channel cells → more interference
- Trade-off between capacity and interference

### Co-channel Reuse Distance (D)

The **co-channel reuse distance** is the minimum distance between cells using the same frequency. This distance determines the co-channel interference level.

$D = R\sqrt{3N}$

**Where:**
- D = Co-channel reuse distance
- R = Cell radius (center to vertex of hexagon)
- N = Cluster size

**Derivation:**
For hexagonal geometry with cluster size N, cells using the same frequency are separated by √(3N) cell radii. This can be verified geometrically or using the formula D² = 3N × R².

**Co-channel Reuse Ratio (Q):**

$Q = \frac{D}{R} = \sqrt{3N}$

This dimensionless ratio is independent of cell size and depends only on cluster size.

| Cluster Size (N) | Q = D/R | Co-channel Distance |
|------------------|---------|---------------------|
| 1 | 1.73 | Very close (CDMA only) |
| 3 | 3.00 | Close |
| 4 | 3.46 | Moderate |
| 7 | 4.58 | Standard (GSM) |
| 12 | 6.00 | Large separation |
| 19 | 7.55 | Very large separation |

```
[Diagram: Co-channel Reuse Distance]

              Cell using         Cell using
              frequency f₁       frequency f₁
                  ●                   ●
                 ╱│╲                 ╱│╲
                ╱ │ ╲               ╱ │ ╲
               ╱  │  ╲             ╱  │  ╲
              ╱   │R  ╲           ╱   │R  ╲
             ╱    │    ╲─────────╱    │    ╲
                  ↑     D = R√3N      ↑
            Co-channel            Co-channel
               cell                  cell
```

### Signal-to-Interference Ratio (SIR) Analysis

The quality of communication depends on the signal-to-interference ratio. In a frequency reuse system, the main interference comes from co-channel cells (cells using the same frequency).

**First-Tier Interference Model:**
For hexagonal cells, each cell has 6 co-channel interferers in the first tier (closest ring of co-channel cells):

```
[Diagram: First-Tier Co-channel Interferers]

                    Interferer 1
                         ●
                        ╱ ╲
            Interferer 6   Interferer 2
                 ●           ●
                  ╲         ╱
                   ╲       ╱
                    ●─────● 
                   Serving
                    Cell
                   ╱       ╲
                  ╱         ╲
            Interferer 5   Interferer 3
                 ●           ●
                        ╲ ╱
                         ●
                    Interferer 4
                    
    6 co-channel cells at distance D from serving cell
```

**SIR Calculation:**

Assuming all base stations transmit equal power P, and path loss follows d⁻ⁿ:
- Signal power from serving BS at mobile: S = P × R⁻ⁿ
- Interference from each co-channel BS: Iᵢ ≈ P × D⁻ⁿ (approximating all at distance D)
- Total interference from 6 co-channel cells: I = 6 × P × D⁻ⁿ

$SIR = \frac{S}{I} = \frac{P \cdot R^{-n}}{6 \cdot P \cdot D^{-n}} = \frac{1}{6}\left(\frac{D}{R}\right)^n = \frac{(\sqrt{3N})^n}{6} = \frac{(3N)^{n/2}}{6}$

**For typical urban environment with n = 4:**
$SIR = \frac{(3N)^2}{6} = \frac{9N^2}{6} = 1.5N^2$

**In decibels:**
$SIR(dB) = 10\log_{10}(1.5N^2) = 10\log_{10}(1.5) + 20\log_{10}(N) = 1.76 + 20\log_{10}(N)$

**SIR for Different Cluster Sizes (n=4):**

| N | Q = √3N | SIR (linear) | SIR (dB) |
|---|---------|--------------|----------|
| 3 | 3.00 | 13.5 | 11.3 dB |
| 4 | 3.46 | 24.0 | 13.8 dB |
| 7 | 4.58 | 73.5 | 18.7 dB |
| 12 | 6.00 | 216 | 23.3 dB |

**Minimum SIR Requirements:**
- Analog FM (AMPS): ~18 dB → N = 7
- Digital GSM: ~9-12 dB → N = 3-4 possible with DTX, power control
- CDMA: ~7 dB → N = 1 with power control

### System Capacity Analysis

**Total Channels Available:**
If S = total number of channels allocated to the system:

**Channels per Cell:**
$
