// Dynamic Web Audio API Sound Synthesizer
const AudioSynth = {
  ctx: null,
  aeratorNode: null,
  waterExchangeNode: null,
  
  init() {
    if (!this.ctx) {
      this.ctx = new (window.AudioContext || window.webkitAudioContext)();
    }
    if (this.ctx && this.ctx.state === 'suspended') {
      this.ctx.resume();
    }
  },
  
  playFeed() {
    this.init();
    if (!this.ctx) return;
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    osc.connect(gain);
    gain.connect(this.ctx.destination);
    const now = this.ctx.currentTime;
    osc.type = 'sine';
    osc.frequency.setValueAtTime(350, now);
    osc.frequency.exponentialRampToValueAtTime(1400, now + 0.12);
    gain.gain.setValueAtTime(0.35, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.12);
    osc.start(now);
    osc.stop(now + 0.13);
  },
  
  playSquish() {
    this.init();
    if (!this.ctx) return;
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    osc.connect(gain);
    gain.connect(this.ctx.destination);
    const now = this.ctx.currentTime;
    osc.type = 'triangle';
    osc.frequency.setValueAtTime(220, now);
    osc.frequency.exponentialRampToValueAtTime(40, now + 0.15);
    gain.gain.setValueAtTime(0.60, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.15);
    osc.start(now);
    osc.stop(now + 0.16);
  },
  
  playCrunch() {
    this.init();
    if (!this.ctx) return;
    const now = this.ctx.currentTime;
    const bufferSize = this.ctx.sampleRate * 0.18;
    const buffer = this.ctx.createBuffer(1, bufferSize, this.ctx.sampleRate);
    const data = buffer.getChannelData(0);
    for (let i = 0; i < bufferSize; i++) {
      const t = i / bufferSize;
      const noise = Math.random() * 2 - 1;
      const mod = Math.sin(t * 120);
      data[i] = noise * (1 - t) * (mod > 0 ? 0.7 : 0.2);
    }
    const noiseNode = this.ctx.createBufferSource();
    noiseNode.buffer = buffer;
    const gain = this.ctx.createGain();
    gain.gain.setValueAtTime(0.55, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.18);
    noiseNode.connect(gain);
    gain.connect(this.ctx.destination);
    noiseNode.start(now);
    noiseNode.stop(now + 0.19);
  },
  
  playClick() {
    this.init();
    if (!this.ctx) return;
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    osc.connect(gain);
    gain.connect(this.ctx.destination);
    const now = this.ctx.currentTime;
    osc.type = 'sine';
    osc.frequency.setValueAtTime(650, now);
    gain.gain.setValueAtTime(0.30, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.04);
    osc.start(now);
    osc.stop(now + 0.05);
  },
  
  playWin() {
    this.init();
    if (!this.ctx) return;
    const now = this.ctx.currentTime;
    const notes = [261.63, 329.63, 392.00, 523.25]; // C4, E4, G4, C5 arpeggio
    notes.forEach((freq, idx) => {
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(freq, now + idx * 0.12);
      gain.gain.setValueAtTime(0.40, now + idx * 0.12);
      gain.gain.exponentialRampToValueAtTime(0.001, now + idx * 0.12 + 0.35);
      osc.start(now + idx * 0.12);
      osc.stop(now + idx * 0.12 + 0.36);
    });
  },
  
  playLose() {
    this.init();
    if (!this.ctx) return;
    const now = this.ctx.currentTime;
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    osc.connect(gain);
    gain.connect(this.ctx.destination);
    osc.type = 'sawtooth';
    osc.frequency.setValueAtTime(330, now);
    osc.frequency.linearRampToValueAtTime(110, now + 0.65);
    gain.gain.setValueAtTime(0.45, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.65);
    osc.start(now);
    osc.stop(now + 0.66);
  },

  playAeratorToggle(isOn) {
    this.init();
    if (!this.ctx) return;
    const now = this.ctx.currentTime;
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    osc.connect(gain);
    gain.connect(this.ctx.destination);
    
    osc.type = 'triangle';
    if (isOn) {
      // Upward chirpy double tone (water wheel start)
      osc.frequency.setValueAtTime(300, now);
      osc.frequency.setValueAtTime(550, now + 0.08);
      
      // Keep volume loud for both notes, then decay
      gain.gain.setValueAtTime(0.45, now);
      gain.gain.setValueAtTime(0.45, now + 0.07);
      gain.gain.linearRampToValueAtTime(0.01, now + 0.22);
      
      osc.start(now);
      osc.stop(now + 0.23);
    } else {
      // Downward double tone (water wheel stop)
      osc.frequency.setValueAtTime(450, now);
      osc.frequency.setValueAtTime(250, now + 0.08);
      
      // Keep volume loud for both notes, then decay
      gain.gain.setValueAtTime(0.40, now);
      gain.gain.setValueAtTime(0.40, now + 0.07);
      gain.gain.linearRampToValueAtTime(0.01, now + 0.22);
      
      osc.start(now);
      osc.stop(now + 0.23);
    }
  },

  playWaterExchangeToggle(isOn) {
    this.init();
    if (!this.ctx) return;
    const now = this.ctx.currentTime;
    
    if (isOn) {
      // Swoosh upward sweep (water exchange open)
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.type = 'sine';
      osc.frequency.setValueAtTime(200, now);
      osc.frequency.exponentialRampToValueAtTime(800, now + 0.25);
      gain.gain.setValueAtTime(0.35, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.25);
      osc.start(now);
      osc.stop(now + 0.26);
    } else {
      // Descending drop sweep (water exchange close)
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.type = 'sine';
      osc.frequency.setValueAtTime(600, now);
      osc.frequency.exponentialRampToValueAtTime(150, now + 0.22);
      gain.gain.setValueAtTime(0.30, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.22);
      osc.start(now);
      osc.stop(now + 0.23);
    }
  },

  startAeratorSound() {
    this.init();
    if (!this.ctx) return;
    if (this.aeratorNode) return; // already playing
    
    const now = this.ctx.currentTime;
    const osc = this.ctx.createOscillator();
    const oscGain = this.ctx.createGain();
    
    osc.type = 'triangle';
    osc.frequency.setValueAtTime(90, now); // Low motor hum
    oscGain.gain.setValueAtTime(0.05, now); // Soft background level
    
    const lfo = this.ctx.createOscillator();
    const lfoGain = this.ctx.createGain();
    lfo.frequency.setValueAtTime(6, now); // 6 Hz rotation speed
    lfoGain.gain.setValueAtTime(25, now);
    
    lfo.connect(lfoGain);
    lfoGain.connect(osc.frequency);
    
    osc.connect(oscGain);
    oscGain.connect(this.ctx.destination);
    
    lfo.start(now);
    osc.start(now);
    
    this.aeratorNode = { osc, lfo, oscGain };
  },

  stopAeratorSound() {
    if (!this.aeratorNode || !this.ctx) return;
    const now = this.ctx.currentTime;
    const node = this.aeratorNode;
    this.aeratorNode = null;
    
    node.oscGain.gain.linearRampToValueAtTime(0.001, now + 0.15);
    setTimeout(() => {
      try {
        node.osc.stop();
        node.lfo.stop();
      } catch (e) {}
    }, 200);
  },

  startWaterExchangeSound() {
    this.init();
    if (!this.ctx) return;
    if (this.waterExchangeNode) return; // already playing
    
    const now = this.ctx.currentTime;
    const bufferSize = this.ctx.sampleRate * 2;
    const buffer = this.ctx.createBuffer(1, bufferSize, this.ctx.sampleRate);
    const data = buffer.getChannelData(0);
    for (let i = 0; i < bufferSize; i++) {
      data[i] = Math.random() * 2 - 1;
    }
    
    const noiseSource = this.ctx.createBufferSource();
    noiseSource.buffer = buffer;
    noiseSource.loop = true;
    
    const filter = this.ctx.createBiquadFilter();
    filter.type = 'lowpass';
    filter.frequency.setValueAtTime(450, now); // deep flow sound
    
    const gain = this.ctx.createGain();
    gain.gain.setValueAtTime(0.04, now); // Soft background level
    
    noiseSource.connect(filter);
    filter.connect(gain);
    gain.connect(this.ctx.destination);
    
    noiseSource.start(now);
    
    this.waterExchangeNode = { noiseSource, gain };
  },

  stopWaterExchangeSound() {
    if (!this.waterExchangeNode || !this.ctx) return;
    const now = this.ctx.currentTime;
    const node = this.waterExchangeNode;
    this.waterExchangeNode = null;
    
    node.gain.gain.linearRampToValueAtTime(0.001, now + 0.15);
    setTimeout(() => {
      try {
        node.noiseSource.stop();
      } catch (e) {}
    }, 200);
  },

  // --- BACKGROUND MUSIC RESERVATION (背景音樂預留區) ---
  // You can easily enable/disable BGM by toggling this flag.
  // To play an audio file, uncomment the code inside startBgm() and supply a valid URL to your music file.
  bgmNode: null,
  bgmEnabled: true, // Set this to true to enable BGM

  startBgm() {
    if (!this.bgmEnabled) return;
    this.init();
    if (!this.ctx) return;
    if (this.bgmNode) return; // Already playing

    const now = this.ctx.currentTime;
    
    // METHOD 2: HTML5 Audio Element (For playing external MP3/MP4 music files)
    // Plays the audio track of the uploaded bckmusic.mp4 file in a continuous loop.
    try {
      const audio = new Audio();
      audio.src = "/static/water/assets/bckmusic.mp4";
      audio.loop = true;
      audio.volume = 0.22; // Keep background music soft and balanced
      
      audio.play().catch(e => {
        console.warn("Autoplay blocked or playback failed:", e);
      });
      
      this.bgmNode = { audio, type: 'audio_file' };
    } catch (e) {
      console.warn("Failed to start audio file BGM:", e);
    }
  },

  stopBgm() {
    if (!this.bgmNode) return;
    const node = this.bgmNode;
    this.bgmNode = null;
    
    try {
      if (node.type === 'synth') {
        node.osc1.stop();
        node.osc2.stop();
      } else if (node.type === 'audio_file') {
        node.audio.pause();
        node.audio.src = ""; // release resource
      }
    } catch (e) {
      console.warn("Failed to stop BGM", e);
    }
  },

  pauseBgm() {
    if (!this.bgmNode) return;
    try {
      if (this.bgmNode.type === 'synth') {
        this.bgmNode.gainNode.gain.value = 0; // mute
      } else if (this.bgmNode.type === 'audio_file') {
        this.bgmNode.audio.pause();
      }
    } catch (e) {}
  },

  resumeBgm() {
    if (!this.bgmNode) return;
    try {
      if (this.bgmNode.type === 'synth') {
        this.bgmNode.gainNode.gain.value = 0.015; // unmute
      } else if (this.bgmNode.type === 'audio_file') {
        this.bgmNode.audio.play();
      }
    } catch (e) {}
  }
};

// Global Game State
const state = {
  gameStarted: false,
  gameActive: false,
  instructionsCleared: false,
  timeRemaining: 60,
  growth: 0,
  aeratorOn: false,
  waterExchangeOn: false,
  feedCount: 0,
  aerateCount: 0,
  clamCount: 4,
  water: {
    temperature: 27.2,
    ph: 7.4,
    oxygen: 6.5,
    turbidity: 20,
    dynamicVal: 50 // Algae density %
  },
  messages: [],
  isGameOverReason: "", // "oxygen_depletion", "water_pollution", "clam_annihilation" or ""
  oxygenWarningTimer: 0,
  pollutionWarningTimer: 0,
  nextCrabSpawnInterval: Math.random() * 4 + 8, // random between 8 and 12 seconds
  leaderboardSource: "result",
  clams: [],
  activePellets: [],
  rottingPelletsCount: 0,
  activeCrabs: []
};

const AR_FEED_SCORE_URL = "score/";
const AR_FEED_LEADERBOARD_URL = "leaderboard/";

function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(";").shift();
  return "";
}

// Global helper for food pellets eating mechanism
function eatFoodPellet(pelletEl, points = 2.5) {
  if (pelletEl.dataset.eaten === "true") return;
  pelletEl.dataset.eaten = "true";
  
  // Quick scale down animation
  pelletEl.setAttribute('animation__shrink', 'property: scale; to: 0.01 0.01 0.01; dur: 150');
  
  state.growth = Math.min(100, state.growth + points);
  
  // Trigger DOM cleanup
  setTimeout(() => {
    pelletEl.remove();
  }, 150);
}

AFRAME.registerComponent('disable-root-motion', {
  tick: function () {
    const mesh = this.el.getObject3D('mesh');
    if (mesh) {
      const targets = ['Sketchfab_model', 'RootNode', 'SKM_Trout', 'Line01'];
      targets.forEach((name) => {
        const obj = mesh.getObjectByName(name);
        if (obj) {
          obj.position.set(0, 0, 0);
        }
      });
    }
  }
});

// A-Frame component for Milkfish Wander & Flocking Simulation
AFRAME.registerComponent('fish-swim-simulation', {
  schema: {
    speed: { type: 'number', default: 0.09 }, // base swimming speed (m/s)
    boundsRadius: { type: 'number', default: 0.52 },
    separationDistance: { type: 'number', default: 0.16 }
  },
  init: function () {
    this.randomPhase = Math.random() * Math.PI * 2;
    this.velocity = new THREE.Vector3(
      Math.random() - 0.5,
      (Math.random() - 0.5) * 0.1,
      Math.random() - 0.5
    ).normalize().multiplyScalar(this.data.speed);
    
    this.wanderAngle = Math.random() * Math.PI * 2;

    // Cache list of other milkfish to avoid DOM query on every frame
    this.otherFish = null;

    // Pre-allocated vectors to eliminate GC overhead in high-frequency tick loop
    this.wanderForce = new THREE.Vector3();
    this.boundaryForce = new THREE.Vector3();
    this.heightForce = new THREE.Vector3();
    this.separationForce = new THREE.Vector3();
    this.diffVec = new THREE.Vector3();
    this.foodForce = new THREE.Vector3();
    this.aeratorAvoidanceForce = new THREE.Vector3();
    this.steerForce = new THREE.Vector3();
  },
  tick: function (time, timeDelta) {
    const isDead = (state.isGameOverReason === "oxygen_depletion" || state.isGameOverReason === "water_pollution" || state.water.oxygen < 2.0);
    if (!state.gameActive && !isDead) return;

    const dt = Math.min(timeDelta / 1000, 0.1);
    const pos = this.el.object3D.position;

    if (isDead) {
      // 1. Float to surface Y = 0.085
      if (pos.y < 0.085) {
        pos.y = Math.min(0.085, pos.y + 0.02 * dt);
      } else {
        // Gentle bobbing on the surface
        pos.y = 0.085 + 0.002 * Math.sin(time / 400 + this.randomPhase);
      }
      // Slow drift
      pos.x += 0.0025 * Math.sin(time / 2000 + this.randomPhase) * dt;
      pos.z += 0.0025 * Math.cos(time / 2000 + this.randomPhase) * dt;

      // Clamp position within boundaries
      const distXZ = Math.sqrt(pos.x * pos.x + pos.z * pos.z);
      if (distXZ > 0.56) {
        pos.x = (pos.x / distXZ) * 0.56;
        pos.z = (pos.z / distXZ) * 0.56;
      }

      // Rotate: roll 180 degrees (belly-up), keep current heading yaw, pitch 0
      const currentRotation = this.el.getAttribute('rotation') || { x: 0, y: 0, z: 0 };
      this.el.setAttribute('rotation', { x: 0, y: currentRotation.y, z: 180 });
      return;
    }

    const isChoking = (state.water.oxygen < 3.0);

    // 1. Wander Force
    this.wanderForce.set(
      Math.cos(this.wanderAngle),
      0,
      Math.sin(this.wanderAngle)
    ).multiplyScalar(isChoking ? 0.015 : 0.04);
    this.wanderAngle += (Math.random() - 0.5) * 0.6;

    // 2. Boundary Avoidance Force
    const distXZ = Math.sqrt(pos.x * pos.x + pos.z * pos.z);
    this.boundaryForce.set(0, 0, 0);
    if (distXZ > this.data.boundsRadius) {
      this.boundaryForce.set(-pos.x, 0, -pos.z).normalize().multiplyScalar((distXZ - this.data.boundsRadius) * 2.5);
    }

    // 3. Depth Constraints (Water is at height 0.09, stay submerged. If choking, float to gulp air)
    this.heightForce.set(0, 0, 0);
    const minY = isChoking ? 0.072 : 0.035;
    const maxY = isChoking ? 0.086 : 0.08;
    if (pos.y < minY) {
      this.heightForce.y = (minY - pos.y) * 2.0;
    } else if (pos.y > maxY) {
      this.heightForce.y = (maxY - pos.y) * 2.0;
    } else {
      // Natural vertical bobbing
      this.heightForce.y = 0.002 * Math.sin(time / 500 + this.randomPhase);
    }

    // 4. Separation Force (avoid colliding with other fish wrappers)
    this.separationForce.set(0, 0, 0);
    if (!this.otherFish) {
      this.otherFish = Array.from(document.querySelectorAll('.milkfish-wrapper'));
    }
    let neighborsCount = 0;
    this.otherFish.forEach(other => {
      if (other === this.el) return;
      const otherPos = other.object3D.position;
      const d = pos.distanceTo(otherPos);
      if (d < this.data.separationDistance && d > 0.001) {
        this.diffVec.copy(pos).sub(otherPos).normalize().divideScalar(d);
        this.separationForce.add(this.diffVec);
        neighborsCount++;
        // Apply vertical separation bias to break symmetry
        if (pos.y > otherPos.y) {
          this.separationForce.y += 0.02;
        } else {
          this.separationForce.y -= 0.02;
        }
      }
    });
    if (neighborsCount > 0) {
      this.separationForce.multiplyScalar(0.06);
    }

    // 5. Food Pellets Attraction Force (only if not choking)
    this.foodForce.set(0, 0, 0);
    const pellets = state.activePellets || [];
    let closestPellet = null;
    let minDist = 999;
    
    if (!isChoking) {
      pellets.forEach(pellet => {
        if (pellet.dataset.rotting === "true") return; // ignore rotting food
        const pelletPos = pellet.object3D.position;
        const d = pos.distanceTo(pelletPos);
        if (d < minDist && d < 0.28) {
          minDist = d;
          closestPellet = pellet;
        }
      });

      if (closestPellet) {
        const targetPos = closestPellet.object3D.position;
        this.foodForce.subVectors(targetPos, pos).normalize().multiplyScalar(0.35);
        
        // Eat pellet when close
        if (minDist < 0.048) {
          eatFoodPellet(closestPellet, 2.0); // fish gains score
        }
      }
    }

    // 6. Aerator Avoidance Force (Steer away from aerator assembly at x = -0.50, z = 0)
    this.aeratorAvoidanceForce.set(0, 0, 0);
    const aeratorX = -0.50;
    const aeratorZ = 0;
    const dx = pos.x - aeratorX;
    const dz = pos.z - aeratorZ;
    const distToAerator = Math.sqrt(dx * dx + dz * dz);
    if (distToAerator < 0.16) {
      const forceMag = (0.16 - distToAerator) * 4.0;
      if (distToAerator > 0.001) {
        this.aeratorAvoidanceForce.set(dx, 0, dz).normalize().multiplyScalar(forceMag);
      } else {
        this.aeratorAvoidanceForce.set(1, 0, 0).multiplyScalar(forceMag);
      }
    }

    // Combine Steering Forces
    this.steerForce.set(0, 0, 0)
      .add(this.wanderForce)
      .add(this.boundaryForce)
      .add(this.heightForce)
      .add(this.separationForce)
      .add(this.foodForce)
      .add(this.aeratorAvoidanceForce);

    // Update Velocity
    this.velocity.addScaledVector(this.steerForce, dt);
    
    // Clamp velocities depending on whether they target food
    const speed = this.velocity.length();
    const baseSpeed = this.data.speed * (isChoking ? 0.35 : 1.0);
    const targetSpeed = closestPellet && !isChoking ? this.data.speed * 1.8 : baseSpeed;
    if (speed > targetSpeed) {
      this.velocity.normalize().multiplyScalar(targetSpeed);
    } else if (speed < baseSpeed * 0.5) {
      this.velocity.normalize().multiplyScalar(baseSpeed * 0.5);
    }

    // Apply Position
    pos.addScaledVector(this.velocity, dt);

    // Hard Boundary Constraints
    const hardDistXZ = Math.sqrt(pos.x * pos.x + pos.z * pos.z);
    if (hardDistXZ > 0.56) {
      pos.x = (pos.x / hardDistXZ) * 0.56;
      pos.z = (pos.z / hardDistXZ) * 0.56;
      this.velocity.reflect(new THREE.Vector3(-pos.x, 0, -pos.z).normalize());
    }
    pos.y = Math.min(0.085, Math.max(0.03, pos.y));

    // Align rotation with velocity direction (head-first)
    const yaw = Math.atan2(this.velocity.x, this.velocity.z) * 180 / Math.PI + 180;
    const speedXZ = Math.sqrt(this.velocity.x * this.velocity.x + this.velocity.z * this.velocity.z);
    let pitch = Math.atan2(this.velocity.y, speedXZ) * 180 / Math.PI;

    if (isChoking) {
      // Tilt head up slightly to gasp for air
      pitch = Math.max(pitch, 15);
    }

    this.el.setAttribute('rotation', { x: pitch, y: yaw, z: 0 });
  }
});

// A-Frame component for Shrimps crawling randomly on the floor
AFRAME.registerComponent('shrimp-move-simulation', {
  schema: {
    speed: { type: 'number', default: 0.015 },
    boundsRadius: { type: 'number', default: 0.52 },
    bobAmp: { type: 'number', default: 0.001 },
    pitchAmp: { type: 'number', default: 1.5 },
    rollAmp: { type: 'number', default: 0.8 },
    freq: { type: 'number', default: 3.5 }
  },
  init: function () {
    this.randomPhase = Math.random() * Math.PI * 2;
    this.velocity = new THREE.Vector3(
      Math.random() - 0.5,
      0,
      Math.random() - 0.5
    ).normalize().multiplyScalar(this.data.speed);
    
    this.wanderAngle = Math.random() * Math.PI * 2;

    // Pre-allocated vectors to eliminate GC overhead in high-frequency tick loop
    this.wanderForce = new THREE.Vector3();
    this.boundaryForce = new THREE.Vector3();
    this.foodForce = new THREE.Vector3();
    this.aeratorAvoidanceForce = new THREE.Vector3();
    this.steerForce = new THREE.Vector3();
    this.reflectNormal = new THREE.Vector3();
  },
  tick: function (time, timeDelta) {
    const isDead = (state.isGameOverReason === "oxygen_depletion" || state.isGameOverReason === "water_pollution" || state.water.oxygen < 2.0);
    if (!state.gameActive && !isDead) return;

    const dt = Math.min(timeDelta / 1000, 0.1);
    const pos = this.el.object3D.position;

    if (isDead) {
      // Remain at bottom Y = 0.015, gentle bobbing
      pos.y = 0.015 + 0.001 * Math.sin(time / 600 + this.randomPhase);
      
      // Roll 180 degrees (belly-up) on floor
      const currentRotation = this.el.getAttribute('rotation') || { x: 0, y: 0, z: 0 };
      this.el.setAttribute('rotation', { x: 0, y: currentRotation.y, z: 180 });
      return;
    }

    const isChoking = (state.water.oxygen < 3.0);

    // 1. Wander Force
    this.wanderForce.set(
      Math.cos(this.wanderAngle),
      0,
      Math.sin(this.wanderAngle)
    ).multiplyScalar(isChoking ? 0.01 : 0.03);
    this.wanderAngle += (Math.random() - 0.5) * 0.6;

    // 2. Boundary Avoidance
    const distXZ = Math.sqrt(pos.x * pos.x + pos.z * pos.z);
    this.boundaryForce.set(0, 0, 0);
    if (distXZ > this.data.boundsRadius) {
      this.boundaryForce.set(-pos.x, 0, -pos.z).normalize().multiplyScalar((distXZ - this.data.boundsRadius) * 2.0);
    }

    // 3. Food Attraction (only if not choking)
    this.foodForce.set(0, 0, 0);
    const pellets = state.activePellets || [];
    let closestPellet = null;
    let minDist = 999;
    
    if (!isChoking) {
      pellets.forEach(pellet => {
        const pelletPos = pellet.object3D.position;
        const d = pos.distanceTo(pelletPos);
        if (d < minDist && d < 0.22) {
          minDist = d;
          closestPellet = pellet;
        }
      });

      if (closestPellet) {
        const targetPos = closestPellet.object3D.position;
        this.foodForce.set(targetPos.x - pos.x, 0, targetPos.z - pos.z).normalize().multiplyScalar(0.3);
        
        // Eat pellet when close
        if (minDist < 0.038) {
          const isRotting = closestPellet.dataset.rotting === "true";
          eatFoodPellet(closestPellet, isRotting ? 1.5 : 2.5); // Shrimps clean pond bottom
        }
      }
    }

    // 4. Aerator Avoidance Force (Steer away from aerator assembly at x = -0.50, z = 0)
    this.aeratorAvoidanceForce.set(0, 0, 0);
    const aeratorX = -0.50;
    const aeratorZ = 0;
    const dx = pos.x - aeratorX;
    const dz = pos.z - aeratorZ;
    const distToAerator = Math.sqrt(dx * dx + dz * dz);
    if (distToAerator < 0.16) {
      const forceMag = (0.16 - distToAerator) * 4.0;
      if (distToAerator > 0.001) {
        this.aeratorAvoidanceForce.set(dx, 0, dz).normalize().multiplyScalar(forceMag);
      } else {
        this.aeratorAvoidanceForce.set(1, 0, 0).multiplyScalar(forceMag);
      }
    }

    // Combine forces
    this.steerForce.set(0, 0, 0)
      .add(this.wanderForce)
      .add(this.boundaryForce)
      .add(this.foodForce)
      .add(this.aeratorAvoidanceForce);

    this.velocity.addScaledVector(this.steerForce, dt);
    
    // Clamp speed
    const speed = this.velocity.length();
    const baseSpeed = this.data.speed * (isChoking ? 0.35 : 1.0);
    const targetSpeed = closestPellet && !isChoking ? this.data.speed * 1.5 : baseSpeed;
    if (speed > targetSpeed) {
      this.velocity.normalize().multiplyScalar(targetSpeed);
    } else if (speed < baseSpeed * 0.5) {
      this.velocity.normalize().multiplyScalar(baseSpeed * 0.5);
    }

    // Update Position on X-Z floor
    pos.x += this.velocity.x * dt;
    pos.z += this.velocity.z * dt;

    // Hard Boundary Constraints
    const hardDistXZ = Math.sqrt(pos.x * pos.x + pos.z * pos.z);
    if (hardDistXZ > 0.56) {
      pos.x = (pos.x / hardDistXZ) * 0.56;
      pos.z = (pos.z / hardDistXZ) * 0.56;
      this.reflectNormal.set(-pos.x, 0, -pos.z).normalize();
      this.velocity.reflect(this.reflectNormal);
    }

    // Vertical wiggle close to the bottom ground Y=0.015
    const t = (time / 1000) * this.data.freq + this.randomPhase;
    pos.y = 0.015 + this.data.bobAmp * Math.sin(t);

    // Yaw heading aligned with movement (and child mesh rotated +270 to align head-first)
    const yaw = Math.atan2(this.velocity.x, this.velocity.z) * 180 / Math.PI + 180;
    const pitch = this.data.pitchAmp * Math.sin(t) * (isChoking ? 0.2 : 1.0);
    const roll = this.data.rollAmp * Math.cos(t * 2.0) * (isChoking ? 0.2 : 1.0);

    this.el.setAttribute('rotation', { x: pitch, y: yaw, z: roll });
  }
});

// A-Frame component for Food Pellets sinking and rotting
AFRAME.registerComponent('food-pellet', {
  init: function () {
    this.sunk = false;
    this.spawnTime = Date.now();
  },
  tick: function (time, timeDelta) {
    if (!state.gameActive) return;

    const dt = timeDelta / 1000;
    const pos = this.el.object3D.position;

    if (pos.y > 0.02) {
      // Sinks slowly to the floor (2 cm/s)
      pos.y -= 0.02 * dt;
    } else {
      if (!this.sunk) {
        this.sunk = true;
        // Pellet turns brown/rotting color when reaching the floor
        this.el.setAttribute('material', 'color: #7f5539; roughness: 0.9');
        this.el.dataset.rotting = "true";
      }

      // Rotting decay penalty per second
      state.water.oxygen = Math.max(3.2, state.water.oxygen - 0.08 * dt);
      state.water.turbidity = Math.min(85, state.water.turbidity + 0.3 * dt);

      // Deletes itself after 4 seconds of rotting to avoid layout clutter
      if (Date.now() - this.spawnTime > 8000) {
        this.el.remove();
      }
    }
  }
});

document.addEventListener("DOMContentLoaded", () => {
  window.addEventListener('pointerdown', () => {
    AudioSynth.init();
  }, { once: true });

  const initialNode = document.getElementById("initial-water-data");
  const glbExistsNode = document.getElementById("glb-exists-data");

  const initialWaterData = initialNode
    ? JSON.parse(initialNode.textContent)
    : { temperature: 27.2, ph: 7.4, oxygen: 6.5, turbidity: 20 };

  const glbExists = glbExistsNode
    ? JSON.parse(glbExistsNode.textContent)
    : { milkfish: false, shrimp: false, clam: false, fish: false };

  function cleanupGLTFModel(evt) {
    const model = evt.detail.model;
    if (!model) return;

    // Hide calibration target cubes or helper tools in GLB files
    const hideTargets = ['Cube_2', 'Object_4', '_Cube_0', 'Cube_0'];
    hideTargets.forEach((name) => {
      const targetNode = model.getObjectByName(name);
      if (targetNode) targetNode.visible = false;
    });

    model.traverse((child) => {
      if (child.name && (
        child.name.toLowerCase().includes('colorchecker') ||
        child.name.toLowerCase().includes('calibration') ||
        child.name.toLowerCase().includes('color_checker') ||
        child.name.toLowerCase() === 'object_4' ||
        child.name.toLowerCase() === '_cube_0' ||
        child.name.toLowerCase() === 'cube_0'
      )) {
        child.visible = false;
      }
    });
  }

  // Base scale adjustments for GLTF models when loaded
  const glbBaseScale = {
    milkfish: { x: 0.55, y: 0.55, z: 0.55 },
    shrimp: { x: 0.03, y: 0.03, z: 0.03 },
    clam: { x: 0.012, y: 0.012, z: 0.012 },
    fish: { x: 0.03, y: 0.03, z: 0.03 },
    crab: { x: 1.7, y: 1.7, z: 1.7 }
  };

  // Base rotation adjustments for GLTF models when loaded
  const glbBaseRotation = {
    milkfish: "0 180 0",
    shrimp: "0 270 0",
    clam: "90 0 0",
    fish: "0 90 0",
    crab: "0 180 0"
  };

  // Scene Configuration (Dedicated to Clam Polyculture Pond)
  const pondConfig = {
    name: "文蛤混養體驗池",
    desc: "水面點擊投放飼料；點擊螃蟹進行除害。虱目魚控制水面藻相，白蝦清理池底殘餌，平衡生態。",
    targets: [],
    dynamicLabel: "藻類密度",
    dynamicUnit: "%",
    arTitle: "CLAM POND",
    initialWater: {
      oxygen: 6.5,
      turbidity: 20,
      dynamicVal: 50,
      temperature: Number(initialWaterData.temperature || 27.2),
      ph: Number(initialWaterData.ph || 7.4)
    }
  };

  const weatherEvents = [
    {
      title: "⛈️ 午後雷陣雨",
      desc: "暴雨降臨！泥沙被沖入漁塭使濁度急升，池水溶氧也快速下降！",
      effect: (water) => {
        water.oxygen = clamp(water.oxygen - 1.8, 1.5, 8.5);
        water.turbidity = clamp(water.turbidity + 18, 5, 85);
      }
    },
    {
      title: "☀️ 烈日曝曬",
      desc: "氣溫炎熱！陽光促使池底浮游藻類迅速暴增，池水溫度隨之上升！",
      effect: (water) => {
        water.dynamicVal = clamp(water.dynamicVal + 20, 0, 100);
        water.temperature = clamp(water.temperature + 1.5, 22.0, 34.0);
        water.oxygen = clamp(water.oxygen - 0.8, 1.5, 8.5);
      }
    },
    {
      title: "💨 季風吹拂",
      desc: "強風掠過池面！增加了溶氧含量，同時水溫有些微下降。",
      effect: (water) => {
        water.oxygen = clamp(water.oxygen + 1.2, 1.5, 8.5);
        water.temperature = clamp(water.temperature - 1.0, 22.0, 34.0);
      }
    }
  ];

  const el = {
    markerStatus: document.getElementById("markerStatus"),
    temperatureVal: document.getElementById("temperatureVal"),
    oxygenVal: document.getElementById("oxygenVal"),
    turbidityVal: document.getElementById("turbidityVal"),
    statusVal: document.getElementById("statusVal"),
    dynamicMetricRow: document.getElementById("dynamicMetricRow"),
    dynamicMetricLabel: document.getElementById("dynamicMetricLabel"),
    dynamicMetricVal: document.getElementById("dynamicMetricVal"),
    sceneName: document.getElementById("sceneName"),
    sceneDesc: document.getElementById("sceneDesc"),
    roundVal: document.getElementById("roundVal"),
    actionButtonsContainer: document.getElementById("actionButtonsContainer"),
    restartBtn: document.getElementById("restartBtn"),
    growthVal: document.getElementById("growthVal"),
    growthBar: document.getElementById("growthBar"),
    growthPercentVal: document.getElementById("growthPercentVal"),
    messageLog: document.getElementById("messageLog"),
    resultOverlay: document.getElementById("resultOverlay"),
    resultBadge: document.getElementById("resultBadge"),
    resultScore: document.getElementById("resultScore"),
    resultText: document.getElementById("resultText"),
    eventOverlay: document.getElementById("eventOverlay"),
    eventTitle: document.getElementById("eventTitle"),
    eventDesc: document.getElementById("eventDesc"),
    eventCloseBtn: document.getElementById("eventCloseBtn"),
    pondMarker: document.getElementById("pondMarker"),
    aeratorAssembly: document.getElementById("aeratorAssembly"),
    aeratorWheel: document.getElementById("aeratorWheel"),
    aeratorSplashGroup: document.getElementById("aeratorSplashGroup"),
    waterExchangeAssembly: document.getElementById("waterExchangeAssembly"),
    waterExchangeFlowGroup: document.getElementById("waterExchangeFlowGroup"),
    feedGroup: document.getElementById("feedGroup"),
    bubbleGroup: document.getElementById("bubbleGroup"),
    dangerAlert: document.getElementById("dangerAlert"),
    dangerAlertText: document.getElementById("dangerAlertText"),
  };

  let gltfLoaded = false;
  let lastTime = 0;
  let weatherTimer = 0;
  let crabSpawnTimer = 0;
  let lastBubbleTime = 0;
  let lastAeratorSplashTime = 0;
  let lastExchangeTime = 0;

  function clamp(value, min, max) {
    return Math.min(Math.max(value, min), max);
  }

  function formatNumber(value, digits = 1) {
    return Number(value).toFixed(digits);
  }

  function getWaterStatus() {
    const oxygen = state.water.oxygen;
    const turbidity = state.water.turbidity;
    const algae = state.water.dynamicVal;

    if (oxygen < 4.5 || turbidity > 55 || algae < 20 || algae > 80) {
      return {
        label: "危險",
        className: "status-danger",
        message: "⚠️ 警告：水質嚴重惡化！溶氧不足或藻相失衡，可能導致生物缺氧死亡！"
      };
    }
    if (oxygen < 5.2 || turbidity > 40 || algae < 35 || algae > 68) {
      return {
        label: "注意",
        className: "status-warning",
        message: "⚠️ 注意：水質出現偏差，藻相偏離健康範圍，建議進行換水或增氧調節。"
      };
    }
    return {
      label: "良好",
      className: "status-good",
      message: "✅ 目前水質指標穩定，藻相與溶氧處於健康狀態。"
    };
  }

  function pushMessage(message) {
    state.messages.unshift(message);
    state.messages = state.messages.slice(0, 3);
    el.messageLog.innerHTML = state.messages
      .map((item) => `<div>・${item}</div>`)
      .join("");
  }

  // Swap to GLTF loader if models are available
  function setupGLTFModels() {
    if (gltfLoaded) return;

    function loadGLTFModel(obj, glbPath, baseRotStr) {
      obj.removeAttribute("geometry");
      obj.removeAttribute("material");

      obj.addEventListener("model-loaded", (evt) => {
        cleanupGLTFModel(evt);
        const model = evt.detail.model;

        if (model && model.animations) {
          model.animations.forEach((clip) => {
            clip.tracks = clip.tracks.filter((track) => {
              const isTranslation = track.name.endsWith(".position") || track.name.includes("translation");
              return !isTranslation;
            });
          });
        }
        obj.setAttribute("animation-mixer", "clip: *; loop: repeat; timeScale: 1.0;");
      });

      obj.setAttribute("gltf-model", `url(${glbPath})`);
      obj.setAttribute("disable-root-motion", "");

      // Apply base rotations
      const curRot = obj.getAttribute("rotation") || { x: 0, y: 0, z: 0 };
      let curRotX = 0, curRotY = 0, curRotZ = 0;
      if (typeof curRot === 'string') {
        const parts = curRot.split(" ").map(Number);
        curRotX = parts[0] || 0;
        curRotY = parts[1] || 0;
        curRotZ = parts[2] || 0;
      } else {
        curRotX = curRot.x || 0;
        curRotY = curRot.y || 0;
        curRotZ = curRot.z || 0;
      }

      const baseRotParts = (baseRotStr || "0 0 0").split(" ").map(Number);
      const baseRotX = baseRotParts[0] || 0;
      const baseRotY = baseRotParts[1] || 0;
      const baseRotZ = baseRotParts[2] || 0;

      obj.setAttribute("rotation", `${curRotX + baseRotX} ${curRotY + baseRotY} ${curRotZ + baseRotZ}`);
    }

    document.querySelectorAll(".milkfish-member").forEach((obj) => {
      if (glbExists.milkfish) {
        loadGLTFModel(obj, "/static/water/assets/milkfish.glb", glbBaseRotation.milkfish);
      }
    });

    document.querySelectorAll(".shrimp-member").forEach((obj) => {
      if (glbExists.shrimp) {
        loadGLTFModel(obj, "/static/water/assets/shrimp.glb", glbBaseRotation.shrimp);
      }
    });

    document.querySelectorAll(".clam-member").forEach((obj) => {
      if (glbExists.clam) {
        loadGLTFModel(obj, "/static/water/assets/clam.glb", glbBaseRotation.clam);
      }
    });

    gltfLoaded = true;



    console.log("[AR] Loaded compressed Draco GLTF models into scene.");
  }  function drawRoundedRect(ctx, x, y, width, height, radius) {
    ctx.beginPath();
    ctx.moveTo(x + radius, y);
    ctx.lineTo(x + width - radius, y);
    ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
    ctx.lineTo(x + width, y + height - radius);
    ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
    ctx.lineTo(x + radius, y + height);
    ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
    ctx.lineTo(x, y + radius);
    ctx.quadraticCurveTo(x, y, x + radius, y);
    ctx.closePath();
  }

  function updateARScene() {
    const status = getWaterStatus();
    const pondBase = document.getElementById("pondBase");
    const dangerRing = document.getElementById("dangerRing");

    if (!pondBase) return;

    setupGLTFModels();

    // Toggle tint colors based on water status & algae bloom
    let waterColor = "#168aad";
    let statusColor = "#80ed99"; // Green

    const algae = state.water.dynamicVal;
    if (algae > 70) {
      waterColor = "#2d5a27"; // Overly thick green water
    } else if (algae < 30) {
      waterColor = "#90e0ef"; // Overly clear water
    }

    if (status.label === "注意") {
      waterColor = "#d9a441";
      statusColor = "#ffd166"; // Yellow
    }
    if (status.label === "危險") {
      waterColor = "#b23a48";
      statusColor = "#ff6b6b"; // Red
    }

    pondBase.setAttribute("material", `color: ${waterColor}; opacity: 0.45; transparent: true`);

    if (dangerRing) {
      dangerRing.setAttribute("visible", status.label === "危險");
    }

    // Draw text and indicators onto HTML canvas texture
    const canvas = document.getElementById("arPanelCanvas");
    if (canvas) {
      const ctx = canvas.getContext("2d");
      
      // Clear canvas
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      // Background (glassmorphic translucent dark blue)
      ctx.fillStyle = "rgba(0, 43, 58, 0.50)";
      drawRoundedRect(ctx, 0, 0, canvas.width, canvas.height, 24);
      ctx.fill();
      
      // Cyber border
      ctx.strokeStyle = "rgba(126, 232, 255, 0.4)";
      ctx.lineWidth = 4;
      ctx.stroke();
      
      // Font styles
      ctx.textBaseline = "top";
      
      // Title: 文蛤混養體驗池
      ctx.font = "bold 32px 'Noto Sans TC', sans-serif";
      ctx.fillStyle = "#7ee8ff";
      ctx.fillText("文蛤混養體驗池", 36, 28);
      
      // Status Label: 良好 / 注意 / 危險
      ctx.font = "bold 34px 'Noto Sans TC', sans-serif";
      ctx.fillStyle = statusColor;
      ctx.textAlign = "right";
      ctx.fillText(status.label, canvas.width - 36, 26);
      ctx.textAlign = "left"; // reset alignment
      
      // Metrics text details
      ctx.font = "26px 'Noto Sans TC', sans-serif";
      ctx.fillStyle = "#ffffff";
      ctx.fillText(`溶氧量：${state.water.oxygen.toFixed(1)} mg/L`, 36, 90);
      ctx.fillText(`濁度值：${Math.round(state.water.turbidity)} NTU`, 36, 140);
      ctx.fillText(`藻類密度：${Math.round(state.water.dynamicVal)}%`, 36, 190);
      
      // Draw oxygen bar background
      ctx.fillStyle = "rgba(51, 92, 103, 0.8)";
      drawRoundedRect(ctx, 36, 242, 440, 18, 9);
      ctx.fill();
      
      // Draw oxygen bar fill
      const oxygenScale = clamp(state.water.oxygen / 6.5, 0.1, 1.0);
      ctx.fillStyle = statusColor;
      drawRoundedRect(ctx, 36, 242, 440 * oxygenScale, 18, 9);
      ctx.fill();
      
      // Trigger Three.js material map update
      const plane = document.getElementById("arWaterPlane");
      if (plane && plane.getObject3D('mesh')) {
        const material = plane.getObject3D('mesh').material;
        if (material.map) {
          material.map.needsUpdate = true;
        }
      }
    }
  }
  function updateUI() {
    const status = getWaterStatus();

    el.oxygenVal.textContent = `${formatNumber(state.water.oxygen)} mg/L`;
    el.turbidityVal.textContent = `${Math.round(state.water.turbidity)} NTU`;
    el.temperatureVal.textContent = `${formatNumber(state.water.temperature)} °C`;
    el.statusVal.textContent = status.label;
    el.statusVal.className = status.className;

    el.dynamicMetricLabel.textContent = pondConfig.dynamicLabel;
    el.dynamicMetricVal.textContent = `${Math.round(state.water.dynamicVal)} ${pondConfig.dynamicUnit}`;

    el.sceneName.textContent = pondConfig.name;
    el.sceneDesc.textContent = pondConfig.desc;
    el.roundVal.textContent = state.timeRemaining;
    if (el.growthVal) {
      el.growthVal.textContent = Math.round(state.growth);
    }

    const growthPercent = clamp(state.growth, 0, 100);
    if (el.growthBar) {
      el.growthBar.style.width = `${growthPercent}%`;
    }
    if (el.growthPercentVal) {
      el.growthPercentVal.textContent = `${Math.round(growthPercent)}%`;
    }

    // Visual model size changes based on biological growth
    const scaleFactor = 1.0 + (state.growth * 0.006);

    document.querySelectorAll(".milkfish-member").forEach((fish) => {
      if (glbExists.milkfish) {
        const s = scaleFactor * glbBaseScale.milkfish.x;
        fish.setAttribute("scale", `${s} ${s} ${s}`);
      } else {
        fish.setAttribute("scale", `${scaleFactor} ${scaleFactor} ${scaleFactor}`);
      }
    });

    document.querySelectorAll(".shrimp-member").forEach((shrimp) => {
      if (glbExists.shrimp) {
        const s = scaleFactor * glbBaseScale.shrimp.x;
        shrimp.setAttribute("scale", `${s} ${s} ${s}`);
      } else {
        shrimp.setAttribute("scale", `${scaleFactor} ${scaleFactor} ${scaleFactor}`);
      }
    });

    document.querySelectorAll(".clam-member").forEach((clam) => {
      if (glbExists.clam) {
        const s = scaleFactor * glbBaseScale.clam.x;
        clam.setAttribute("scale", `${s} ${s} ${s}`);
      } else {
        clam.setAttribute("scale", `${scaleFactor * 1.35} ${scaleFactor * 0.45} ${scaleFactor}`);
      }
    });

    updateActionButtons();
    updateARScene();
  }

  function renderActionButtons() {
    el.actionButtonsContainer.innerHTML = "";

    // Aerator Button
    const aerateBtn = document.createElement("button");
    aerateBtn.id = "aerateBtn";
    aerateBtn.className = `action-btn ${state.aeratorOn ? 'btn-action-primary' : 'btn-action-sub'}`;
    aerateBtn.textContent = state.aeratorOn ? "🔌 關閉曝氣水車" : "💨 開啟曝氣水車";
    aerateBtn.addEventListener("click", () => {
      if (state.timeRemaining <= 0) return;
      state.aeratorOn = !state.aeratorOn;
      AudioSynth.playAeratorToggle(state.aeratorOn);
      if (state.aeratorOn) {
        AudioSynth.startAeratorSound();
      } else {
        AudioSynth.stopAeratorSound();
      }
      updateAeratorVisual(0);
      pushMessage(state.aeratorOn ? "⚡ 啟動增氧水車！消耗成長值但能持續提升溶氧。" : "🔌 關閉增氧水車。");
      updateActionButtons();
    });
    el.actionButtonsContainer.appendChild(aerateBtn);

    // Water Exchange Button
    const exchangeBtn = document.createElement("button");
    exchangeBtn.id = "exchangeBtn";
    exchangeBtn.className = `action-btn ${state.waterExchangeOn ? 'btn-action-primary' : 'btn-action-sub'}`;
    exchangeBtn.textContent = state.waterExchangeOn ? "🛑 停止換水" : "💧 引水換水";
    exchangeBtn.addEventListener("click", () => {
      if (state.timeRemaining <= 0) return;
      state.waterExchangeOn = !state.waterExchangeOn;
      AudioSynth.playWaterExchangeToggle(state.waterExchangeOn);
      if (state.waterExchangeOn) {
        AudioSynth.startWaterExchangeSound();
      } else {
        AudioSynth.stopWaterExchangeSound();
      }
      updateWaterExchangeVisual();
      pushMessage(state.waterExchangeOn ? "🌊 開始引水調節！持續控制藻相並降低濁度。" : "🛑 停止引水調節。");
      updateActionButtons();
    });
    el.actionButtonsContainer.appendChild(exchangeBtn);

    // Finish Experience Button
    const finishBtn = document.createElement("button");
    finishBtn.id = "finishBtn";
    finishBtn.className = "action-btn btn-action-finish";
    finishBtn.textContent = "完成體驗";
    finishBtn.addEventListener("click", () => {
      AudioSynth.playClick();
      finishExperience();
    });
    el.actionButtonsContainer.appendChild(finishBtn);
  }

  function updateActionButtons() {
    const aerateBtn = document.getElementById("aerateBtn");
    if (aerateBtn) {
      aerateBtn.className = `action-btn ${state.aeratorOn ? 'btn-action-primary' : 'btn-action-sub'}`;
      aerateBtn.textContent = state.aeratorOn ? "🔌 關閉曝氣水車" : "💨 開啟曝氣水車";
    }

    const exchangeBtn = document.getElementById("exchangeBtn");
    if (exchangeBtn) {
      exchangeBtn.className = `action-btn ${state.waterExchangeOn ? 'btn-action-primary' : 'btn-action-sub'}`;
      exchangeBtn.textContent = state.waterExchangeOn ? "🛑 停止換水" : "💧 引水換水";
    }
  }

  // --- AR SPATIAL CLICK RAYCAST INTERACTION ---
  function setupSpatialTapListener() {
    const scene = document.querySelector('a-scene');
    if (!scene) return;

    window.addEventListener('pointerdown', (e) => {
      if (!state.gameActive || state.timeRemaining <= 0) return;

      // Filter out clicks on overlay menus or DOM HUD components
      if (
        e.target.closest('.control-panel') ||
        e.target.closest('.water-panel') ||
        e.target.closest('.top-hud') ||
        e.target.closest('.event-overlay') ||
        e.target.closest('.result-overlay') ||
        e.target.closest('button') ||
        e.target.closest('a')
      ) {
        return;
      }

      const camera = scene.camera;
      if (!camera) return;

      const raycaster = new THREE.Raycaster();
      const mouse = new THREE.Vector2();

      mouse.x = (e.clientX / window.innerWidth) * 2 - 1;
      mouse.y = -(e.clientY / window.innerHeight) * 2 + 1;
      raycaster.setFromCamera(mouse, camera);

      // Check Crab collision squishing first
      const crabs = Array.from(document.querySelectorAll('.crab-pest'));
      let clickedCrab = null;

      for (let crabEl of crabs) {
        const intersectsCrab = raycaster.intersectObjects(crabEl.object3D.children, true);
        if (intersectsCrab.length > 0) {
          clickedCrab = crabEl;
          break;
        }
      }

      if (clickedCrab) {
        squishCrab(clickedCrab);
        return;
      }

      // Check Pond surface collision for dropping food pellets
      const pondBase = document.getElementById('pondBase');
      if (!pondBase) return;

      const intersectsPond = raycaster.intersectObject(pondBase.getObject3D('mesh'));
      if (intersectsPond.length > 0) {
        const localPoint = intersectsPond[0].point.clone();
        const pondGroup = document.getElementById('pondGroup');
        if (pondGroup) {
          // Translate global intersection point to local target space
          pondGroup.object3D.worldToLocal(localPoint);
          
          // Spawn food pellet inside target pond
          spawnFeedPellet(localPoint.x, localPoint.z);
        }
      }
    });
  }

  // Spawn feeding pellet at local coordinate
  function spawnFeedPellet(x, z) {
    if (!el.feedGroup) return;

    AudioSynth.playFeed();

    const pellet = document.createElement("a-sphere");
    pellet.className = "food-pellet";
    pellet.setAttribute("radius", "0.012");
    pellet.setAttribute("material", "color: #ffca3a; opacity: 1.0; roughness: 0.5");
    pellet.setAttribute("position", `${x} 0.08 ${z}`);
    pellet.setAttribute("food-pellet", ""); // Attach falling logic component
    pellet.dataset.rotting = "false";
    pellet.dataset.eaten = "false";

    el.feedGroup.appendChild(pellet);
  }

  // Squish target crab pest
  function squishCrab(crabEl) {
    if (crabEl.dataset.squished === "true") return;
    crabEl.dataset.squished = "true";

    AudioSynth.playSquish();

    state.growth = Math.min(100, state.growth + 10);
    pushMessage("💥 成功消滅螃蟹侵入者！獲得成長值 +10。");

    // Flatten squash animation
    crabEl.setAttribute('animation', 'property: scale; to: 1 0.05 1; dur: 200; easing: easeOutQuad');
    
    // Fade elements (including the red target ring)
    crabEl.querySelectorAll('a-box, a-sphere, a-ring').forEach(child => {
      child.setAttribute('animation__fade', 'property: material.opacity; to: 0; dur: 400');
      child.setAttribute('material', 'transparent: true');
    });

    setTimeout(() => {
      crabEl.remove();
    }, 400);
  }

  function getTargetClamWithLeastTargeters(clams, excludingCrab) {
    if (clams.length === 0) return null;
    
    const counts = {};
    clams.forEach(c => {
      counts[c.id] = 0;
    });
    
    const crabs = document.querySelectorAll('.crab-pest');
    crabs.forEach(crab => {
      if (crab === excludingCrab || crab.dataset.squished === "true") return;
      const targetId = crab.dataset.targetId;
      if (counts[targetId] !== undefined) {
        counts[targetId]++;
      }
    });
    
    let minCount = 999;
    clams.forEach(c => {
      if (counts[c.id] < minCount) {
        minCount = counts[c.id];
      }
    });
    
    const candidateClams = clams.filter(c => counts[c.id] === minCount);
    return candidateClams[Math.floor(Math.random() * candidateClams.length)];
  }

  // Spawn Pest Crab from edges crawling towards a random clam
  function spawnCrab() {
    const pondGroup = document.getElementById('pondGroup');
    if (!pondGroup) return;

    // Filter living clams by eaten status
    const clams = Array.from(document.querySelectorAll('.clam-member')).filter(c => c.dataset.eaten !== 'true');
    if (clams.length === 0) return; // No clams left

    const targetClam = getTargetClamWithLeastTargeters(clams, null);
    if (!targetClam) return;

    // Get position of target clam
    const clamPos = targetClam.getAttribute('position');
    let clamX = 0, clamZ = 0;
    if (typeof clamPos === 'string') {
      const parts = clamPos.split(" ").map(Number);
      clamX = parts[0];
      clamZ = parts[2];
    } else {
      clamX = clamPos.x || 0;
      clamZ = clamPos.z || 0;
    }

    let startX, startZ;
    if (Math.random() < 0.70) {
      // 70% chance: spawn near the target clam (dist 0.16m to 0.24m)
      const spawnAngle = Math.random() * Math.PI * 2;
      const spawnDist = 0.16 + Math.random() * 0.08; // 0.16m to 0.24m away
      
      let testX = clamX + Math.cos(spawnAngle) * spawnDist;
      let testZ = clamZ + Math.sin(spawnAngle) * spawnDist;
      
      // Keep it within pond boundary (0.52m radius)
      const distFromCenter = Math.sqrt(testX * testX + testZ * testZ);
      if (distFromCenter > 0.52) {
        const scale = 0.52 / distFromCenter;
        testX *= scale;
        testZ *= scale;
      }
      startX = testX;
      startZ = testZ;
    } else {
      // 30% chance: spawn at the outer edge of the pond
      const angle = Math.random() * Math.PI * 2;
      startX = 0.52 * Math.cos(angle);
      startZ = 0.52 * Math.sin(angle);
    }

    const crab = document.createElement('a-entity');
    crab.className = 'crab-pest';
    crab.setAttribute('position', `${startX} 0.015 ${startZ}`);
    crab.dataset.targetId = targetClam.id;
    crab.dataset.speed = "0.026"; // Crawl speed (m/s)
    crab.dataset.squished = "false";

    // Adding a red glowing target ring at the bottom of the crab so it is always visible/tappable (enlarged for mobile usability)
    const ring = document.createElement('a-ring');
    ring.setAttribute('radius-inner', '0.12');
    ring.setAttribute('radius-outer', '0.13');
    ring.setAttribute('rotation', '-90 0 0');
    ring.setAttribute('material', 'color: #ff3b3b; shader: flat; opacity: 0.85; transparent: true; depthWrite: false');
    ring.setAttribute('animation', 'property: scale; from: 0.85 0.85 0.85; to: 1.15 1.15 1.15; dir: alternate; dur: 350; loop: true');
    crab.appendChild(ring);

    // Large invisible hit target sphere (radius 0.14m) to make tapping easier on mobile
    const hitBox = document.createElement('a-sphere');
    hitBox.setAttribute('radius', '0.14');
    hitBox.setAttribute('material', 'opacity: 0; transparent: true; depthWrite: false; shader: flat');
    crab.appendChild(hitBox);

    if (glbExists.crab) {
      const model = document.createElement('a-entity');
      model.className = 'crab-member';
      model.setAttribute('gltf-model', 'url(/static/water/assets/crab.glb)');
      const s = glbBaseScale.crab.x;
      model.setAttribute('scale', `${s} ${s} ${s}`);
      model.setAttribute('rotation', '0 180 0'); // Base rotation to align head-first
      model.setAttribute('animation-mixer', 'clip: *; loop: repeat; timeScale: 1.0;');
      
      model.addEventListener('model-loaded', cleanupGLTFModel);
      model.addEventListener('model-error', (err) => {
        console.error("[AR] Crab model load error:", err);
      });
      crab.appendChild(model);
    } else {
      // Body mesh representation
      const body = document.createElement('a-box');
      body.setAttribute('width', '0.04');
      body.setAttribute('height', '0.012');
      body.setAttribute('depth', '0.03');
      body.setAttribute('material', 'color: #d90429; roughness: 0.8');
      crab.appendChild(body);

      const clawL = document.createElement('a-sphere');
      clawL.setAttribute('radius', '0.008');
      clawL.setAttribute('position', '-0.018 0.005 0.014');
      clawL.setAttribute('material', 'color: #ef233c');
      crab.appendChild(clawL);

      const clawR = document.createElement('a-sphere');
      clawR.setAttribute('radius', '0.008');
      clawR.setAttribute('position', '0.018 0.005 0.014');
      clawR.setAttribute('material', 'color: #ef233c');
      crab.appendChild(clawR);
    }

    pondGroup.appendChild(crab);
    pushMessage("🦀 警告：一隻害蟲螃蟹侵入池底！快點擊消滅牠以免咬食文蛤！");
  }

  // Reusable vector to prevent Vector2 creation GC in updateCrabCrawling
  const crabDirVec = new THREE.Vector2();

  // Crawl crab towards target clam
  function updateCrabCrawling(dt) {
    const crabs = state.activeCrabs || [];
    crabs.forEach(crab => {
      if (crab.dataset.squished === "true") return;

      const targetId = crab.dataset.targetId;
      const targetClam = document.getElementById(targetId);
      
      // If target clam is dead or gone, re-target a living one with least targeters
      if (!targetClam || targetClam.dataset.eaten === "true") {
        const clams = state.clams.filter(c => c.dataset.eaten !== 'true');
        const newTargetClam = getTargetClamWithLeastTargeters(clams, crab);
        if (newTargetClam) {
          crab.dataset.targetId = newTargetClam.id;
        } else {
          // No clams left, just crawl around randomly
          crab.dataset.squished = "true";
          crab.remove();
          return;
        }
        return;
      }

      const crabPos = crab.object3D.position;
      const clamPos = targetClam.getAttribute('position'); // clam is static, read string/attr
      let clamX = 0, clamZ = 0;
      if (typeof clamPos === 'string') {
        const parts = clamPos.split(" ").map(Number);
        clamX = parts[0];
        clamZ = parts[2];
      } else {
        clamX = clamPos.x || 0;
        clamZ = clamPos.z || 0;
      }

      crabDirVec.set(clamX - crabPos.x, clamZ - crabPos.z);
      const dist = crabDirVec.length();

      if (dist < 0.04) {
        // Crab reaches clam and eats it! Flipped flat dead shell
        targetClam.setAttribute('scale', `${glbBaseScale.clam.x * 1.3} ${glbBaseScale.clam.y * 0.15} ${glbBaseScale.clam.z * 1.3}`);
        targetClam.setAttribute('rotation', '90 45 180');
        targetClam.removeAttribute('class');
        targetClam.dataset.eaten = "true";
        AudioSynth.playCrunch();
        
        // Hide the clam's green ring when eaten
        const ring = document.getElementById(targetClam.id + "_ring");
        if (ring) {
          ring.setAttribute('visible', 'false');
        }
        
        state.growth = Math.max(0, state.growth - 15);
        pushMessage("🚨 慘劇！螃蟹吃掉了一個文蛤！成長值 -15。");
        
        // Remove crab after eating
        crab.remove();
      } else {
        // Crawl towards target
        crabDirVec.normalize();
        const speed = Number(crab.dataset.speed);
        crabPos.x += crabDirVec.x * speed * dt;
        crabPos.z += crabDirVec.y * speed * dt;

        // Face crawl direction
        const yaw = Math.atan2(crabDirVec.x, crabDirVec.y) * 180 / Math.PI + 180;
        crab.setAttribute('rotation', `0 ${yaw} 0`);
      }
    });
  }

  // --- ACTUATOR EFFECT PARTICLES ---

  function spawnSingleBubble() {
    if (!el.bubbleGroup) return;
    const bubble = document.createElement("a-sphere");
    const x = (Math.random() - 0.5) * 0.45;
    const z = (Math.random() - 0.5) * 0.45;
    const size = 0.005 + Math.random() * 0.012;

    bubble.setAttribute("radius", String(size));
    bubble.setAttribute("material", "color: #caf0f8; opacity: 0.7; transparent: true");
    bubble.setAttribute("position", `${x} 0.015 ${z}`);
    bubble.setAttribute("animation", `property: position; to: ${x} 0.088 ${z}; dur: 850; easing: easeOutQuad`);
    bubble.setAttribute("animation__fade", `property: material.opacity; from: 0.7; to: 0; delay: 550; dur: 300`);

    el.bubbleGroup.appendChild(bubble);
    setTimeout(() => {
      bubble.remove();
    }, 900);
  }

  function updateAeratorVisual(dt) {
    if (!el.aeratorAssembly || !el.aeratorWheel) return;

    el.aeratorAssembly.setAttribute("visible", state.aeratorOn ? "true" : "false");
    if (!state.aeratorOn) return;

    const rotation = el.aeratorWheel.object3D.rotation;
    rotation.z -= dt * 12.5;
  }

  function spawnAeratorSplash() {
    if (!el.aeratorSplashGroup) return;

    const splash = document.createElement("a-sphere");
    const x = 0.018 + Math.random() * 0.05;
    const y = -0.018 + Math.random() * 0.035;
    const z = (Math.random() - 0.5) * 0.06;
    const endX = x + 0.045 + Math.random() * 0.05;
    const endY = y + 0.025 + Math.random() * 0.035;
    const endZ = z + (Math.random() - 0.5) * 0.06;
    const size = 0.004 + Math.random() * 0.007;

    splash.setAttribute("radius", String(size));
    splash.setAttribute("material", "color: #caf0f8; opacity: 0.72; transparent: true");
    splash.setAttribute("position", `${x} ${y} ${z}`);
    splash.setAttribute("animation", `property: position; to: ${endX} ${endY} ${endZ}; dur: 420; easing: easeOutQuad`);
    splash.setAttribute("animation__fade", "property: material.opacity; from: 0.72; to: 0; delay: 180; dur: 240");

    el.aeratorSplashGroup.appendChild(splash);
    setTimeout(() => {
      splash.remove();
    }, 460);
  }

  function updateWaterExchangeVisual() {
    if (!el.waterExchangeAssembly) return;
    el.waterExchangeAssembly.setAttribute("visible", state.waterExchangeOn ? "true" : "false");
  }

  function spawnWaterExchangeStream() {
    if (!el.waterExchangeFlowGroup) return;

    const stream = document.createElement("a-sphere");
    const x = -0.135 + Math.random() * 0.018;
    const y = 0.006 + Math.random() * 0.010;
    const z = (Math.random() - 0.5) * 0.022;
    const endX = x - 0.105 - Math.random() * 0.045;
    const endY = y - 0.018 - Math.random() * 0.008;
    const endZ = z + (Math.random() - 0.5) * 0.034;
    const size = 0.005 + Math.random() * 0.007;

    stream.setAttribute("radius", String(size));
    stream.setAttribute("material", "color: #7ee8ff; opacity: 0.78; transparent: true; depthWrite: false");
    stream.setAttribute("position", `${x} ${y} ${z}`);
    stream.setAttribute("animation", `property: position; to: ${endX} ${endY} ${endZ}; dur: 520; easing: easeOutQuad`);
    stream.setAttribute("animation__fade", "property: material.opacity; from: 0.78; to: 0; delay: 260; dur: 240");

    el.waterExchangeFlowGroup.appendChild(stream);
    setTimeout(() => {
      stream.remove();
    }, 560);
  }

  function spawnExchangeParticle() {
    if (!el.feedGroup) return;
    const particle = document.createElement("a-sphere");
    
    // Flow inward from the nozzle tip (located at radius ~0.51m, angle ~-0.64 rad)
    const angle = -0.64 + (Math.random() - 0.5) * 0.15;
    const startX = 0.51 * Math.cos(angle);
    const startZ = 0.51 * Math.sin(angle);
    const endX = 0.14 * Math.cos(angle + 0.15);
    const endZ = 0.14 * Math.sin(angle + 0.15);

    particle.setAttribute("radius", "0.007");
    particle.setAttribute("material", "color: #90e0ef; opacity: 0.75; transparent: true");
    particle.setAttribute("position", `${startX} 0.10 ${startZ}`);
    particle.setAttribute("animation", `property: position; to: ${endX} 0.03 ${endZ}; dur: 1100; easing: easeOutQuad`);
    particle.setAttribute("animation__fade", `property: material.opacity; from: 0.75; to: 0; delay: 750; dur: 350`);

    el.feedGroup.appendChild(particle);
    setTimeout(() => {
      particle.remove();
    }, 1200);
  }

  // --- DYNAMIC GAME LOOP UPDATE ---
  function updateGame(time) {
    if (!lastTime) lastTime = time;
    const dt = Math.min((time - lastTime) / 1000, 0.1);
    lastTime = time;
    updateAeratorVisual(dt);
    updateWaterExchangeVisual();

    // Cache dynamic arrays once per frame to optimize boids, collision, and rotting checks
    state.activePellets = Array.from(document.querySelectorAll('.food-pellet'));
    state.rottingPelletsCount = state.activePellets.filter(p => p.dataset.rotting === "true").length;
    state.activeCrabs = Array.from(document.querySelectorAll('.crab-pest'));

    if (state.gameActive && state.timeRemaining > 0) {
      // 1. Natural Parameter decays & Rotting Food penalties
      const rottingPellets = state.rottingPelletsCount;
      
      // Base oxygen decay is faster to encourage active aeration
      const o2Decay = -0.075 * dt - (rottingPellets * 0.035 * dt);
      state.water.oxygen = Math.max(1.5, state.water.oxygen + o2Decay);
      
      // Algae bloom and turbidity increase
      const algaeIncrease = 0.07 * dt + (rottingPellets * 0.25 * dt);
      state.water.dynamicVal = Math.min(100, state.water.dynamicVal + algaeIncrease);
      
      const turbidityIncrease = rottingPellets * 0.3 * dt;
      if (turbidityIncrease > 0) {
        state.water.turbidity = Math.min(100, state.water.turbidity + turbidityIncrease);
      }

      // 2. Active Actuator Effects
      if (state.aeratorOn) {
        state.water.oxygen = Math.min(8.5, state.water.oxygen + 0.14 * dt);
        state.water.turbidity = Math.max(5.0, state.water.turbidity - 0.06 * dt);
        state.growth = Math.max(0.0, state.growth - 0.45 * dt); // cost power

        // Spawn bubbles
        if (time - lastBubbleTime > 120) {
          spawnSingleBubble();
          lastBubbleTime = time;
        }

        if (time - lastAeratorSplashTime > 70) {
          spawnAeratorSplash();
          lastAeratorSplashTime = time;
        }
      }

      if (state.waterExchangeOn) {
        state.water.turbidity = Math.max(5.0, state.water.turbidity - 0.55 * dt);
        state.water.dynamicVal = Math.max(0.0, state.water.dynamicVal - 0.8 * dt);
        state.water.temperature = Math.max(22.0, state.water.temperature - 0.06 * dt);
        state.growth = Math.max(0.0, state.growth - 0.65 * dt); // cost water resource

        // Spawn water exchange inward particles
        if (time - lastExchangeTime > 160) {
          spawnExchangeParticle();
          spawnWaterExchangeStream();
          lastExchangeTime = time;
        }
      }

      // 3. Update crawling crabs movement
      updateCrabCrawling(dt);

      // 4. Update Countdown clocks & interval timers
      weatherTimer += dt;
      crabSpawnTimer += dt;

      // Realtime countdown clock ticker (1s)
      if (Math.floor(weatherTimer) >= 1) {
        state.timeRemaining -= 1;
        weatherTimer = 0;
        
        // Trigger weather events every 18 seconds (25% chance)
        if (state.timeRemaining > 5 && state.timeRemaining % 18 === 0 && Math.random() < 0.35) {
          triggerRandomWeatherEvent();
        }

        updateUI();
      }

      // Spawn pest crab every 8 to 12 seconds randomly
      if (crabSpawnTimer >= state.nextCrabSpawnInterval) {
        spawnCrab();
        crabSpawnTimer = 0;
        state.nextCrabSpawnInterval = Math.random() * 4 + 8;
      }

      // 5. Check Early Game Over / Death conditions & Warning alerts
      let showingAlert = false;
      const alertEl = el.dangerAlert;
      const alertTextEl = el.dangerAlertText;

      // Clam Annihilation check
      const livingClams = state.clams.filter(c => c.dataset.eaten !== 'true').length;
      if (livingClams === 0) {
        state.isGameOverReason = "clam_annihilation";
        state.gameActive = false;
        finishExperience();
      }

      // Hypoxia warning & trigger
      if (state.water.oxygen < 3.0) {
        state.oxygenWarningTimer += dt;
        showingAlert = true;
        
        const countdown = Math.max(0, Math.ceil(5.0 - state.oxygenWarningTimer));
        if (alertTextEl) {
          alertTextEl.textContent = `⚠️ 嚴重缺氧！魚蝦即將窒息死亡，剩餘挽救時間：${countdown} 秒！`;
        }
        
        if (state.oxygenWarningTimer >= 5.0) {
          state.isGameOverReason = "oxygen_depletion";
          state.gameActive = false;
          finishExperience();
        }
      } else {
        state.oxygenWarningTimer = 0;
      }

      // Water pollution / toxic algae bloom warning & trigger
      if (!showingAlert && (state.water.dynamicVal > 95.0 || state.water.turbidity > 90.0)) {
        state.pollutionWarningTimer += dt;
        showingAlert = true;
        
        const countdown = Math.max(0, Math.ceil(8.0 - state.pollutionWarningTimer));
        if (alertTextEl) {
          alertTextEl.textContent = `⚠️ 水質嚴重毒化崩壞！剩餘倒池時間：${countdown} 秒！請立即換水！`;
        }
        
        if (state.pollutionWarningTimer >= 8.0) {
          state.isGameOverReason = "water_pollution";
          state.gameActive = false;
          finishExperience();
        }
      } else {
        state.pollutionWarningTimer = 0;
      }

      // Show or hide dangerAlert element
      if (alertEl) {
        if (showingAlert) {
          alertEl.classList.remove("hidden");
        } else {
          alertEl.classList.add("hidden");
        }
      }

      // Game End Check
      if (state.timeRemaining <= 0) {
        state.gameActive = false;
        finishExperience();
      }
    } else {
      // Hide alert when game is inactive
      const alertEl = el.dangerAlert;
      if (alertEl) alertEl.classList.add("hidden");
    }

    requestAnimationFrame(updateGame);
  }

  function triggerRandomWeatherEvent() {
    const ev = weatherEvents[Math.floor(Math.random() * weatherEvents.length)];
    ev.effect(state.water);

    el.eventTitle.textContent = ev.title;
    el.eventDesc.textContent = ev.desc;
    el.eventOverlay.classList.remove("hidden");

    // Pause game during overlay popups
    state.gameActive = false;
  }

  function closeEventModal() {
    el.eventOverlay.classList.add("hidden");
    state.gameActive = true;
    updateUI();
  }

  // --- SCORE & EVALUATION RESULTS ---

  function calculateResult() {
    let score = 0;
    let badge = "";
    let text = "";

    const o2 = state.water.oxygen;
    const turb = state.water.turbidity;
    const algae = state.water.dynamicVal;

    // Count remaining living clams by eaten status
    const livingClams = Array.from(document.querySelectorAll('.clam-member')).filter(c => c.dataset.eaten !== 'true').length;

    // Check early game over reasons
    if (state.isGameOverReason === "oxygen_depletion") {
      score = 0;
      badge = "池區集體缺氧倒池";
      text = "養殖失敗！由於您忽視了溶氧量控制，池水溶氧降至極低的極限值（低於 2.0 mg/L），導致虱目魚與白蝦集體缺氧窒息死亡！在混養中，溶氧是生命線，請記得及時開啟「增氧水車」！";
      return { score, badge, text };
    }

    if (state.isGameOverReason === "water_pollution") {
      score = 5;
      badge = "水質毒化倒池慘劇";
      text = "養殖失敗！投餌過量導致殘餌腐爛，或是放任藻類過度暴增（藻相破表或濁度破表），引發水質毒化崩壞！養殖先養水，水質惡化時請務必使用「換水」功能！";
      return { score, badge, text };
    }

    if (state.isGameOverReason === "clam_annihilation" || livingClams === 0) {
      score = 10;
      badge = "文蛤全滅慘劇";
      text = "很遺憾，所有的文蛤都被入侵的螃蟹吃光了！混養管理中，保護底棲的文蛤是首要任務。請多注意池底動靜並點擊螃蟹將其消滅！";
      return { score, badge, text };
    }

    // Max growth score is 40 points
    score += clamp(state.growth * 0.4, 0, 40);

    // Clam survival score (max 20 points: 5 points per clam)
    score += livingClams * 5;

    // Dissolved oxygen score (max 15 points)
    if (o2 >= 5.5) score += 15;
    else if (o2 >= 4.5) score += 8;
    else score -= 10;

    // Turbidity score (max 12 points)
    if (turb <= 35) score += 12;
    else if (turb <= 50) score += 6;
    else score -= 8;

    // Algae density score (max 13 points)
    if (algae >= 40 && algae <= 65) score += 13;
    else if (algae >= 25 && algae <= 75) score += 7;
    else score -= 8;

    score = clamp(Math.round(score), 0, 100);

    if (score >= 85) {
      badge = "智慧生態養殖大師";
      text = `卓越的決策！你的最終成長值高，且 4 個文蛤存活了 ${livingClams} 個。溶氧、藻相與水溫皆控制在健康範圍，成功展現了「文蛤、白蝦、虱目魚」生態混養的共生優勢！`;
    } else if (score >= 60) {
      badge = "合格池區管理員";
      text = `穩健的管理！你成功維護了文蛤的生存 (${livingClams}/4 存活)。如果能更靈活地開啟增氧水車調解溶氧，或者更迅速地除掉侵入池底的螃蟹，你的成績會更好！`;
    } else {
      badge = "新手實習養殖員";
      text = "水質管理失調或文蛤損失過多。養殖先養水，投餌過多會加速水質劣化；水質過濃或缺氧時記得點擊「換水」與「開啟曝氣」。再挑戰一次吧！";
    }

    return { score, badge, text };
  }

  function saveScoreToServer(result) {
    const name = (typeof GOOGLE_USER_NAME !== 'undefined') ? GOOGLE_USER_NAME : "訪客";
    fetch(AR_FEED_SCORE_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCookie("csrftoken"),
      },
      credentials: "same-origin",
      body: JSON.stringify({
        scene: "clam_polyculture",
        score: result.score,
        badge: result.badge,
        text: result.text,
        growth: state.growth,
        water: state.water,
        player_name: name,
      }),
    }).catch((err) => {
      console.warn("AR leaderboard save failed", err);
    });
  }

  function migrateLocalLeaderboardToServer() {
    const name = (typeof GOOGLE_USER_NAME !== 'undefined') ? GOOGLE_USER_NAME : "訪客";
    const d = new Date();
    const todayStr = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;

    try {
      const leaderboard = JSON.parse(localStorage.getItem("ar_feed_leaderboard") || "[]");
      const existing = leaderboard.find((item) => item.name === name && item.date === todayStr && !String(item.name).includes("(bot)"));
      if (!existing) return;

      fetch(AR_FEED_SCORE_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken"),
        },
        credentials: "same-origin",
        body: JSON.stringify({
          scene: "clam_polyculture",
          score: existing.score,
          badge: "歷史紀錄",
          text: "由此瀏覽器的舊排行榜紀錄同步至資料庫。",
          player_name: name,
        }),
      }).catch((err) => {
        console.warn("AR leaderboard migration failed", err);
      });
    } catch (err) {
      console.warn("AR leaderboard migration skipped", err);
    }
  }

  function finishExperience() {
    state.gameActive = false;
    const result = calculateResult();

    // Trigger Win or Lose sounds
    if (result.score >= 60 && state.isGameOverReason === "") {
      AudioSynth.playWin();
    } else {
      AudioSynth.playLose();
    }

    // Turn off actuators
    state.aeratorOn = false;
    state.waterExchangeOn = false;
    AudioSynth.stopAeratorSound();
    AudioSynth.stopWaterExchangeSound();
    AudioSynth.stopBgm();

    el.resultBadge.textContent = result.badge;
    el.resultScore.textContent = `${result.score} 分`;
    el.resultText.textContent = result.text;

    // Save score to leaderboard array in localStorage (keeping only the highest score per name/account)
    const d = new Date();
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const date = String(d.getDate()).padStart(2, '0');
    const todayStr = `${year}-${month}-${date}`;
    
    const name = (typeof GOOGLE_USER_NAME !== 'undefined') ? GOOGLE_USER_NAME : "匿名者";
    let leaderboard = JSON.parse(localStorage.getItem("ar_feed_leaderboard") || "[]");
    
    const existingIndex = leaderboard.findIndex(item => item.name === name);
    if (existingIndex !== -1) {
      if (result.score > leaderboard[existingIndex].score) {
        leaderboard[existingIndex].score = result.score;
        leaderboard[existingIndex].date = todayStr;
      }
    } else {
      leaderboard.push({
        name: name,
        score: result.score,
        date: todayStr
      });
    }
    leaderboard.sort((a, b) => b.score - a.score);
    leaderboard = leaderboard.slice(0, 10);
    localStorage.setItem("ar_feed_leaderboard", JSON.stringify(leaderboard));

    localStorage.setItem(
      "ar_feed_result",
      JSON.stringify({
        scene: "clam_polyculture",
        score: result.score,
        badge: result.badge,
        text: result.text,
        growth: state.growth,
        water: state.water,
        createdAt: new Date().toISOString(),
      })
    );

    saveScoreToServer(result);

    // If game ended due to disaster, show warning and delay result modal so users can view the belly-up scene
    if (state.isGameOverReason !== "") {
      const alertEl = document.getElementById("dangerAlert");
      const alertTextEl = document.getElementById("dangerAlertText");
      if (alertEl && alertTextEl) {
        alertEl.classList.remove("hidden");
        if (state.isGameOverReason === "oxygen_depletion") {
          alertTextEl.textContent = `💥 嚴重缺氧！漁塭已倒池，正在生成養殖報告...`;
        } else if (state.isGameOverReason === "water_pollution") {
          alertTextEl.textContent = `💥 水質嚴重毒化！漁塭已倒池，正在生成養殖報告...`;
        } else if (state.isGameOverReason === "clam_annihilation") {
          alertTextEl.textContent = `💥 文蛤全滅！守護任務失敗，正在生成養殖報告...`;
        }
      }
      setTimeout(() => {
        if (alertEl) alertEl.classList.add("hidden");
        el.resultOverlay.classList.remove("hidden");
      }, 3500);
    } else {
      el.resultOverlay.classList.remove("hidden");
    }
  }

  function restartExperience() {
    window.location.reload();
  }

  // MindAR Marker Events mapping to game pause/resume logic
  function setupMarkerEvents() {
    if (!el.pondMarker) return;

    el.pondMarker.addEventListener("targetFound", () => {
      el.markerStatus.textContent = "已偵測到標記";
      el.markerStatus.classList.remove("offline");
      el.markerStatus.classList.add("online");

      if (!state.instructionsCleared) {
        return;
      }

      // Auto start/resume when marker is visible
      if (!state.gameStarted) {
        state.gameStarted = true;
        state.gameActive = true;
        AudioSynth.startBgm();
        pushMessage("💡 提示：點擊池水表面可投餵飼料；點擊害蟲螃蟹可將其消滅！");
      } else {
        state.gameActive = true;
        pushMessage("▶️ 重新偵測到圖卡，遊戲繼續。");
        if (state.aeratorOn) AudioSynth.startAeratorSound();
        if (state.waterExchangeOn) AudioSynth.startWaterExchangeSound();
        AudioSynth.resumeBgm();
      }
    });

    el.pondMarker.addEventListener("targetLost", () => {
      el.markerStatus.textContent = "標記離開畫面";
      el.markerStatus.classList.remove("online");
      el.markerStatus.classList.add("offline");

      if (!state.instructionsCleared) {
        return;
      }

      // Pause when target card is lost to prevent tracking failure glitches
      if (state.gameStarted) {
        state.gameActive = false;
        pushMessage("⏸️ 標記離開畫面，遊戲已暫停。");
        AudioSynth.stopAeratorSound();
        AudioSynth.stopWaterExchangeSound();
        AudioSynth.pauseBgm();
      }
    });
  }

  function initLeaderboard() {
    let leaderboard = localStorage.getItem("ar_feed_leaderboard");
    // Clear old mock data to load new bot settings
    if (leaderboard && (leaderboard.includes("林小君") || leaderboard.includes("匿名者1"))) {
      localStorage.removeItem("ar_feed_leaderboard");
      leaderboard = null;
    }
    
    // Specifically filter out old test records of "子科" and "LiaoZike"
    if (leaderboard) {
      try {
        let arr = JSON.parse(leaderboard);
        const filtered = arr.filter(item => item.name !== "子科" && item.name !== "LiaoZike");
        if (filtered.length !== arr.length) {
          localStorage.setItem("ar_feed_leaderboard", JSON.stringify(filtered));
          leaderboard = JSON.stringify(filtered);
        }
      } catch (e) {
        localStorage.removeItem("ar_feed_leaderboard");
        leaderboard = null;
      }
    }
    
    const d = new Date();
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const date = String(d.getDate()).padStart(2, '0');
    const todayStr = `${year}-${month}-${date}`;
    
    if (!leaderboard) {
      const mockData = [
        { name: "睏寶(bot)", score: 75, date: todayStr },
        { name: "藍寶(bot)", score: 65, date: todayStr },
        { name: "痞子妹(bot)", score: 55, date: todayStr },
        { name: "囡囡(bot)", score: 45, date: todayStr }
      ];
      localStorage.setItem("ar_feed_leaderboard", JSON.stringify(mockData));
    }
  }

  function renderLeaderboardItems(scores) {
    const listEl = document.getElementById("leaderboardList");
    if (!listEl) return;

    listEl.innerHTML = "";
    if (!scores.length) {
      listEl.innerHTML = `<div class="leaderboard-item" style="justify-content: center;">今日尚無排行紀錄</div>`;
      return;
    }

    scores.forEach((item, index) => {
      const rank = index + 1;
      let rankClass = `rank-${rank}`;
      let rankIcon = `${rank}`;
      if (rank === 1) rankIcon = "🥇";
      if (rank === 2) rankIcon = "🥈";
      if (rank === 3) rankIcon = "🥉";

      const itemEl = document.createElement("div");
      itemEl.className = `leaderboard-item ${rank <= 3 ? rankClass : ''}`;
      itemEl.innerHTML = `
        <div>
          <span class="rank-badge">${rankIcon}</span>
          <span class="leaderboard-name">${item.name}</span>
        </div>
        <span class="leaderboard-score">${item.score} 分</span>
      `;
      listEl.appendChild(itemEl);
    });
  }

  async function showLeaderboard() {
    const d = new Date();
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const date = String(d.getDate()).padStart(2, '0');
    const todayStr = `${year}-${month}-${date}`;
    
    const dateEl = document.getElementById("leaderboardDate");
    try {
      const response = await fetch(AR_FEED_LEADERBOARD_URL, {
        credentials: "same-origin",
        headers: { "Accept": "application/json" },
      });
      if (response.ok) {
        const data = await response.json();
        if (dateEl && data.date) dateEl.textContent = `今日排行日期：${data.date}`;
        renderLeaderboardItems(data.leaderboard || []);

        const instructionsOverlay = document.getElementById("instructionsOverlay");
        if (instructionsOverlay && !instructionsOverlay.classList.contains("hidden")) {
          instructionsOverlay.classList.add("hidden");
          state.leaderboardSource = "instructions";
        } else {
          state.leaderboardSource = "result";
        }

        document.getElementById("leaderboardOverlay").classList.remove("hidden");
        return;
      }
    } catch (err) {
      console.warn("AR leaderboard load failed", err);
    }
    if (dateEl) dateEl.textContent = `今日日期：${todayStr}`;
    
    let leaderboard = JSON.parse(localStorage.getItem("ar_feed_leaderboard") || "[]");
    
    // Ensure bot entries dynamically update their date so they are always present on today's leaderboard
    leaderboard = leaderboard.map(item => {
      if (item.name.includes("(bot)")) {
        item.date = todayStr;
      }
      return item;
    });
    localStorage.setItem("ar_feed_leaderboard", JSON.stringify(leaderboard));
    const listEl = document.getElementById("leaderboardList");
    if (listEl) {
      listEl.innerHTML = "";
      
      // Filter today's scores
      const todayScores = leaderboard
        .filter(item => item.date === todayStr)
        .sort((a, b) => b.score - a.score);
      
      if (todayScores.length === 0) {
        listEl.innerHTML = `<div class="leaderboard-item" style="justify-content: center;">今日尚無排行紀錄</div>`;
      } else {
        todayScores.forEach((item, index) => {
          const rank = index + 1;
          let rankClass = `rank-${rank}`;
          let rankIcon = `${rank}`;
          if (rank === 1) rankIcon = "🥇";
          if (rank === 2) rankIcon = "🥈";
          if (rank === 3) rankIcon = "🥉";
          
          const itemEl = document.createElement("div");
          itemEl.className = `leaderboard-item ${rank <= 3 ? rankClass : ''}`;
          itemEl.innerHTML = `
            <div>
              <span class="rank-badge">${rankIcon}</span>
              <span class="leaderboard-name">${item.name}</span>
            </div>
            <span class="leaderboard-score">${item.score} 分</span>
          `;
          listEl.appendChild(itemEl);
        });
      }
    }
    
    // Hide instructions if showing leaderboard
    const instructionsOverlay = document.getElementById("instructionsOverlay");
    if (instructionsOverlay && !instructionsOverlay.classList.contains("hidden")) {
      instructionsOverlay.classList.add("hidden");
      state.leaderboardSource = "instructions";
    } else {
      state.leaderboardSource = "result";
    }
    
    document.getElementById("leaderboardOverlay").classList.remove("hidden");
  }

  function setupEvents() {
    el.restartBtn.addEventListener("click", restartExperience);
    el.eventCloseBtn.addEventListener("click", closeEventModal);
    
    const showLbBtn = document.getElementById("showLeaderboardBtn");
    if (showLbBtn) {
      showLbBtn.addEventListener("click", showLeaderboard);
    }
    
    const startLbBtn = document.getElementById("startLeaderboardBtn");
    if (startLbBtn) {
      startLbBtn.addEventListener("click", showLeaderboard);
    }
    
    const backLbBtn = document.getElementById("leaderboardBackBtn");
    if (backLbBtn) {
      backLbBtn.addEventListener("click", () => {
        document.getElementById("leaderboardOverlay").classList.add("hidden");
        // Restore instructions overlay if opened from start screen
        if (state.leaderboardSource === "instructions") {
          const instructionsOverlay = document.getElementById("instructionsOverlay");
          if (instructionsOverlay) {
            instructionsOverlay.classList.remove("hidden");
          }
        }
      });
    }

    const startBtn = document.getElementById("startGameBtn");
    if (startBtn) {
      startBtn.addEventListener("click", () => {
        AudioSynth.init();
        const overlay = document.getElementById("instructionsOverlay");
        if (overlay) overlay.classList.add("hidden");
        state.instructionsCleared = true;
        
        const isOnline = el.markerStatus.classList.contains("online");
        if (isOnline) {
          state.gameStarted = true;
          state.gameActive = true;
          AudioSynth.startBgm();
          pushMessage("💡 提示：點擊池水表面可投餵飼料；點擊害蟲螃蟹可將其消滅！");
        } else {
          pushMessage("請將鏡頭對準 AR 辨識圖卡即可開始體驗！");
        }
      });
    }

    setupSpatialTapListener();
  }

  function init() {
    initLeaderboard();
    migrateLocalLeaderboardToServer();
    setupEvents();
    setupMarkerEvents();
    
    renderActionButtons();

    state.timeRemaining = 60;
    state.growth = 0;
    state.water = { ...pondConfig.initialWater };
    state.messages = [];
    state.clams = Array.from(document.querySelectorAll('.clam-member'));

    // Trigger loop ticking
    requestAnimationFrame(updateGame);

    updateUI();
    pushMessage("請將鏡頭對準 AR 辨識圖卡，看到虛擬漁塭後即自動開始！");
  }

  const scene = document.querySelector("a-scene");
  if (scene) {
    if (scene.hasLoaded) {
      init();
    } else {
      scene.addEventListener("loaded", init);
    }
  } else {
    init();
  }
});
