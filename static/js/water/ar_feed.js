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
  messages: []
};

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
    speed: { type: 'number', default: 0.045 }, // base swimming speed (m/s)
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
  },
  tick: function (time, timeDelta) {
    if (!state.gameActive) return;

    const dt = Math.min(timeDelta / 1000, 0.1);
    const pos = this.el.object3D.position;

    // 1. Wander Force
    const wanderForce = new THREE.Vector3(
      Math.cos(this.wanderAngle),
      0,
      Math.sin(this.wanderAngle)
    ).multiplyScalar(0.04);
    this.wanderAngle += (Math.random() - 0.5) * 0.6;

    // 2. Boundary Avoidance Force
    const distXZ = Math.sqrt(pos.x * pos.x + pos.z * pos.z);
    const boundaryForce = new THREE.Vector3();
    if (distXZ > this.data.boundsRadius) {
      boundaryForce.set(-pos.x, 0, -pos.z).normalize().multiplyScalar((distXZ - this.data.boundsRadius) * 2.5);
    }

    // 3. Depth Constraints (Water is at height 0.09, stay submerged)
    const heightForce = new THREE.Vector3();
    if (pos.y < 0.035) {
      heightForce.y = (0.035 - pos.y) * 2.0;
    } else if (pos.y > 0.08) {
      heightForce.y = (0.08 - pos.y) * 2.0;
    } else {
      // Natural vertical bobbing
      heightForce.y = 0.002 * Math.sin(time / 500 + this.randomPhase);
    }

    // 4. Separation Force (avoid colliding with other fish wrappers)
    const separationForce = new THREE.Vector3();
    const otherFish = document.querySelectorAll('.milkfish-wrapper');
    let neighborsCount = 0;
    otherFish.forEach(other => {
      if (other === this.el) return;
      const otherPos = other.object3D.position;
      const d = pos.distanceTo(otherPos);
      if (d < this.data.separationDistance && d > 0.001) {
        const diff = pos.clone().sub(otherPos).normalize().divideScalar(d);
        separationForce.add(diff);
        neighborsCount++;
        // Apply vertical separation bias to break symmetry
        if (pos.y > otherPos.y) {
          separationForce.y += 0.02;
        } else {
          separationForce.y -= 0.02;
        }
      }
    });
    if (neighborsCount > 0) {
      separationForce.multiplyScalar(0.06);
    }

    // 5. Food Pellets Attraction Force
    const foodForce = new THREE.Vector3();
    const pellets = document.querySelectorAll('.food-pellet');
    let closestPellet = null;
    let minDist = 999;
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
      foodForce.subVectors(targetPos, pos).normalize().multiplyScalar(0.35);
      
      // Eat pellet when close
      if (minDist < 0.048) {
        eatFoodPellet(closestPellet, 2.0); // fish gains score
      }
    }

    // Combine Steering Forces
    const steerForce = new THREE.Vector3()
      .add(wanderForce)
      .add(boundaryForce)
      .add(heightForce)
      .add(separationForce)
      .add(foodForce);

    // Update Velocity
    this.velocity.addScaledVector(steerForce, dt);
    
    // Clamp velocities depending on whether they target food
    const speed = this.velocity.length();
    const targetSpeed = closestPellet ? this.data.speed * 1.6 : this.data.speed;
    if (speed > targetSpeed) {
      this.velocity.normalize().multiplyScalar(targetSpeed);
    } else if (speed < this.data.speed * 0.5) {
      this.velocity.normalize().multiplyScalar(this.data.speed * 0.5);
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
    const pitch = Math.atan2(this.velocity.y, speedXZ) * 180 / Math.PI;

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
  },
  tick: function (time, timeDelta) {
    if (!state.gameActive) return;

    const dt = Math.min(timeDelta / 1000, 0.1);
    const pos = this.el.object3D.position;

    // 1. Wander Force
    const wanderForce = new THREE.Vector3(
      Math.cos(this.wanderAngle),
      0,
      Math.sin(this.wanderAngle)
    ).multiplyScalar(0.03);
    this.wanderAngle += (Math.random() - 0.5) * 0.6;

    // 2. Boundary Avoidance
    const distXZ = Math.sqrt(pos.x * pos.x + pos.z * pos.z);
    const boundaryForce = new THREE.Vector3();
    if (distXZ > this.data.boundsRadius) {
      boundaryForce.set(-pos.x, 0, -pos.z).normalize().multiplyScalar((distXZ - this.data.boundsRadius) * 2.0);
    }

    // 3. Food Attraction (attracted to both fresh and rotting pellets on floor)
    const foodForce = new THREE.Vector3();
    const pellets = document.querySelectorAll('.food-pellet');
    let closestPellet = null;
    let minDist = 999;
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
      foodForce.set(targetPos.x - pos.x, 0, targetPos.z - pos.z).normalize().multiplyScalar(0.3);
      
      // Eat pellet when close
      if (minDist < 0.038) {
        const isRotting = closestPellet.dataset.rotting === "true";
        eatFoodPellet(closestPellet, isRotting ? 1.5 : 2.5); // Shrimps clean pond bottom
      }
    }

    // Combine forces
    const force = new THREE.Vector3()
      .add(wanderForce)
      .add(boundaryForce)
      .add(foodForce);

    this.velocity.addScaledVector(force, dt);
    
    // Clamp speed
    const speed = this.velocity.length();
    const targetSpeed = closestPellet ? this.data.speed * 1.5 : this.data.speed;
    if (speed > targetSpeed) {
      this.velocity.normalize().multiplyScalar(targetSpeed);
    } else if (speed < this.data.speed * 0.5) {
      this.velocity.normalize().multiplyScalar(this.data.speed * 0.5);
    }

    // Update Position on X-Z floor
    pos.x += this.velocity.x * dt;
    pos.z += this.velocity.z * dt;

    // Hard Boundary Constraints
    const hardDistXZ = Math.sqrt(pos.x * pos.x + pos.z * pos.z);
    if (hardDistXZ > 0.56) {
      pos.x = (pos.x / hardDistXZ) * 0.56;
      pos.z = (pos.z / hardDistXZ) * 0.56;
      this.velocity.reflect(new THREE.Vector3(-pos.x, 0, -pos.z).normalize());
    }

    // Vertical wiggle close to the bottom ground Y=0.015
    const t = (time / 1000) * this.data.freq + this.randomPhase;
    pos.y = 0.015 + this.data.bobAmp * Math.sin(t);

    // Yaw heading aligned with movement (and child mesh rotated +270 to align head-first)
    const yaw = Math.atan2(this.velocity.x, this.velocity.z) * 180 / Math.PI + 180;
    const pitch = this.data.pitchAmp * Math.sin(t);
    const roll = this.data.rollAmp * Math.cos(t * 2.0);

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
  const initialNode = document.getElementById("initial-water-data");
  const glbExistsNode = document.getElementById("glb-exists-data");

  const initialWaterData = initialNode
    ? JSON.parse(initialNode.textContent)
    : { temperature: 27.2, ph: 7.4, oxygen: 6.5, turbidity: 20 };

  const glbExists = glbExistsNode
    ? JSON.parse(glbExistsNode.textContent)
    : { milkfish: false, shrimp: false, clam: false, fish: false };

  // Base scale adjustments for GLTF models when loaded
  const glbBaseScale = {
    milkfish: { x: 0.55, y: 0.55, z: 0.55 },
    shrimp: { x: 0.03, y: 0.03, z: 0.03 },
    clam: { x: 0.012, y: 0.012, z: 0.012 },
    fish: { x: 0.03, y: 0.03, z: 0.03 }
  };

  // Base rotation adjustments for GLTF models when loaded
  const glbBaseRotation = {
    milkfish: "0 180 0",
    shrimp: "0 270 0",
    clam: "90 0 0",
    fish: "0 90 0"
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
        water.oxygen = clamp(water.oxygen - 1.2, 3.2, 8.5);
        water.turbidity = clamp(water.turbidity + 18, 5, 85);
      }
    },
    {
      title: "☀️ 烈日曝曬",
      desc: "氣溫炎熱！陽光促使池底浮游藻類迅速暴增，池水溫度隨之上升！",
      effect: (water) => {
        water.dynamicVal = clamp(water.dynamicVal + 20, 0, 100);
        water.temperature = clamp(water.temperature + 1.5, 22.0, 34.0);
        water.oxygen = clamp(water.oxygen - 0.4, 3.2, 8.5);
      }
    },
    {
      title: "💨 季風吹拂",
      desc: "強風掠過池面！增加了溶氧含量，同時水溫有些微下降。",
      effect: (water) => {
        water.oxygen = clamp(water.oxygen + 0.8, 3.2, 8.5);
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
    feedGroup: document.getElementById("feedGroup"),
    bubbleGroup: document.getElementById("bubbleGroup"),
  };

  let gltfLoaded = false;
  let lastTime = 0;
  let weatherTimer = 0;
  let crabSpawnTimer = 0;
  let lastBubbleTime = 0;
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
        const model = evt.detail.model;

        // Hide calibration tools
        const hideTargets = ['Cube_2', 'Object_4'];
        hideTargets.forEach((name) => {
          const targetNode = model.getObjectByName(name);
          if (targetNode) targetNode.visible = false;
        });

        model.traverse((child) => {
          if (child.name && (
            child.name.toLowerCase().includes('colorchecker') ||
            child.name.toLowerCase().includes('calibration') ||
            child.name.toLowerCase().includes('color_checker')
          )) {
            child.visible = false;
          }
        });

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
    const selectedHalo = document.getElementById("selectedHalo");

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

    // Selected halo focus on the first living clam
    const livingClams = Array.from(document.querySelectorAll(".clam-member")).filter(c => c.getAttribute("visible") !== "false");
    if (selectedHalo && livingClams.length > 0) {
      selectedHalo.setAttribute("visible", "true");
      selectedHalo.setAttribute("position", livingClams[0].getAttribute("position"));
    } else if (selectedHalo) {
      selectedHalo.setAttribute("visible", "false");
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
    el.growthVal.textContent = Math.round(state.growth);

    const growthPercent = clamp(state.growth, 0, 100);
    el.growthBar.style.width = `${growthPercent}%`;

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

    renderActionButtons();
    updateARScene();
  }

  function renderActionButtons() {
    el.actionButtonsContainer.innerHTML = "";

    // Aerator Button
    const aerateBtn = document.createElement("button");
    aerateBtn.className = `action-btn ${state.aeratorOn ? 'btn-action-primary' : 'btn-action-sub'}`;
    aerateBtn.textContent = state.aeratorOn ? "🔌 關閉曝氣水車" : "💨 開啟曝氣水車";
    aerateBtn.addEventListener("click", () => {
      if (state.timeRemaining <= 0) return;
      state.aeratorOn = !state.aeratorOn;
      pushMessage(state.aeratorOn ? "⚡ 啟動增氧水車！消耗成長值但能持續提升溶氧。" : "🔌 關閉增氧水車。");
      renderActionButtons();
    });
    el.actionButtonsContainer.appendChild(aerateBtn);

    // Water Exchange Button
    const exchangeBtn = document.createElement("button");
    exchangeBtn.className = `action-btn ${state.waterExchangeOn ? 'btn-action-primary' : 'btn-action-sub'}`;
    exchangeBtn.textContent = state.waterExchangeOn ? "🛑 停止換水" : "💧 引水換水";
    exchangeBtn.addEventListener("click", () => {
      if (state.timeRemaining <= 0) return;
      state.waterExchangeOn = !state.waterExchangeOn;
      pushMessage(state.waterExchangeOn ? "🌊 開始引水調節！持續控制藻相並降低濁度。" : "🛑 停止引水調節。");
      renderActionButtons();
    });
    el.actionButtonsContainer.appendChild(exchangeBtn);

    // Finish Experience Button
    const finishBtn = document.createElement("button");
    finishBtn.className = "action-btn btn-action-finish";
    finishBtn.textContent = "完成體驗";
    finishBtn.addEventListener("click", finishExperience);
    el.actionButtonsContainer.appendChild(finishBtn);
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

    state.growth = Math.min(100, state.growth + 10);
    pushMessage("💥 成功消滅螃蟹侵入者！獲得成長值 +10。");

    // Flatten squash animation
    crabEl.setAttribute('animation', 'property: scale; to: 1 0.05 1; dur: 200; easing: easeOutQuad');
    
    // Fade elements
    crabEl.querySelectorAll('a-box, a-sphere').forEach(child => {
      child.setAttribute('animation__fade', 'property: material.opacity; to: 0; dur: 400');
      child.setAttribute('material', 'transparent: true');
    });

    setTimeout(() => {
      crabEl.remove();
    }, 400);
  }

  // Spawn Pest Crab from edges crawling towards a random clam
  function spawnCrab() {
    const pondGroup = document.getElementById('pondGroup');
    if (!pondGroup) return;

    // Filter living clams
    const clams = Array.from(document.querySelectorAll('.clam-member')).filter(c => c.getAttribute('visible') !== 'false');
    if (clams.length === 0) return; // No clams left

    const targetClam = clams[Math.floor(Math.random() * clams.length)];
    const angle = Math.random() * Math.PI * 2;
    const startX = 0.52 * Math.cos(angle);
    const startZ = 0.52 * Math.sin(angle);

    const crab = document.createElement('a-entity');
    crab.className = 'crab-pest';
    crab.setAttribute('position', `${startX} 0.015 ${startZ}`);
    crab.dataset.targetId = targetClam.id;
    crab.dataset.speed = "0.018"; // Crawl speed (m/s)
    crab.dataset.squished = "false";

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

    pondGroup.appendChild(crab);
    pushMessage("🦀 警告：一隻害蟲螃蟹侵入池底！快點擊消滅牠以免咬食文蛤！");
  }

  // Crawl crab towards target clam
  function updateCrabCrawling(dt) {
    const crabs = document.querySelectorAll('.crab-pest');
    crabs.forEach(crab => {
      if (crab.dataset.squished === "true") return;

      const targetId = crab.dataset.targetId;
      const targetClam = document.getElementById(targetId);
      
      // If target clam is dead or gone, re-target a living one
      if (!targetClam || targetClam.getAttribute('visible') === 'false') {
        const clams = Array.from(document.querySelectorAll('.clam-member')).filter(c => c.getAttribute('visible') !== 'false');
        if (clams.length > 0) {
          crab.dataset.targetId = clams[Math.floor(Math.random() * clams.length)].id;
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

      const dir = new THREE.Vector2(clamX - crabPos.x, clamZ - crabPos.z);
      const dist = dir.length();

      if (dist < 0.04) {
        // Crab reaches clam and eats it!
        targetClam.setAttribute('visible', 'false');
        targetClam.object3D.visible = false;
        
        state.growth = Math.max(0, state.growth - 15);
        pushMessage("🚨 慘劇！螃蟹吃掉了一個文蛤！成長值 -15。");
        
        // Remove crab after eating
        crab.remove();
      } else {
        // Crawl towards target
        dir.normalize();
        const speed = Number(crab.dataset.speed);
        crabPos.x += dir.x * speed * dt;
        crabPos.z += dir.y * speed * dt;

        // Face crawl direction
        const yaw = Math.atan2(dir.x, dir.y) * 180 / Math.PI + 180;
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

  function spawnExchangeParticle() {
    if (!el.feedGroup) return;
    const particle = document.createElement("a-sphere");
    
    // Swirl inwards from edge
    const angle = Math.random() * Math.PI * 2;
    const startX = 0.56 * Math.cos(angle);
    const startZ = 0.56 * Math.sin(angle);
    const endX = 0.18 * Math.cos(angle);
    const endZ = 0.18 * Math.sin(angle);

    particle.setAttribute("radius", "0.007");
    particle.setAttribute("material", "color: #90e0ef; opacity: 0.75; transparent: true");
    particle.setAttribute("position", `${startX} 0.08 ${startZ}`);
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

    if (state.gameActive && state.timeRemaining > 0) {
      // 1. Natural Parameter decays
      state.water.oxygen = Math.max(3.2, state.water.oxygen - 0.035 * dt);
      state.water.dynamicVal = Math.min(100, state.water.dynamicVal + 0.07 * dt);

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
      }

      if (state.waterExchangeOn) {
        state.water.turbidity = Math.max(5.0, state.water.turbidity - 0.55 * dt);
        state.water.dynamicVal = Math.max(0.0, state.water.dynamicVal - 0.8 * dt);
        state.water.temperature = Math.max(22.0, state.water.temperature - 0.06 * dt);
        state.growth = Math.max(0.0, state.growth - 0.65 * dt); // cost water resource

        // Spawn water exchange inward particles
        if (time - lastExchangeTime > 160) {
          spawnExchangeParticle();
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

      // Spawn pest crab every 12 seconds
      if (crabSpawnTimer >= 12) {
        spawnCrab();
        crabSpawnTimer = 0;
      }

      // Game End Check
      if (state.timeRemaining <= 0) {
        state.gameActive = false;
        finishExperience();
      }
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

    // Count remaining living clams
    const livingClams = Array.from(document.querySelectorAll('.clam-member')).filter(c => c.getAttribute('visible') !== 'false').length;

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
    } else if (livingClams === 0) {
      badge = "文蛤全滅慘劇";
      text = "很遺憾，所有的文蛤都被入侵的螃蟹吃光了！混養管理中，除害蟲與防衛也是重要的一環。請多注意池底動靜並點擊螃蟹將其消滅！";
    } else {
      badge = "新手實習養殖員";
      text = "水質管理失調或文蛤損失過多。養殖先養水，投餌過多會加速水質劣化；水質過濃或缺氧時記得點擊「換水」與「開啟曝氣」。再挑戰一次吧！";
    }

    return { score, badge, text };
  }

  function finishExperience() {
    state.gameActive = false;
    const result = calculateResult();

    // Turn off actuators
    state.aeratorOn = false;
    state.waterExchangeOn = false;

    el.resultBadge.textContent = result.badge;
    el.resultScore.textContent = `${result.score} 分`;
    el.resultText.textContent = result.text;

    // Save score to leaderboard array in localStorage
    const todayStr = new Date().toISOString().split('T')[0];
    let leaderboard = JSON.parse(localStorage.getItem("ar_feed_leaderboard") || "[]");
    leaderboard.push({
      name: (typeof GOOGLE_USER_NAME !== 'undefined') ? GOOGLE_USER_NAME : "匿名者",
      score: result.score,
      date: todayStr
    });
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

    el.resultOverlay.classList.remove("hidden");
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
        pushMessage("💡 提示：點擊池水表面可投餵飼料；點擊害蟲螃蟹可將其消滅！");
      } else {
        state.gameActive = true;
        pushMessage("▶️ 重新偵測到圖卡，遊戲繼續。");
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
    
    if (!leaderboard) {
      const todayStr = new Date().toISOString().split('T')[0];
      const mockData = [
        { name: "睏寶(bot)", score: 75, date: todayStr },
        { name: "藍寶(bot)", score: 65, date: todayStr },
        { name: "痞子妹(bot)", score: 55, date: todayStr },
        { name: "囡囡(bot)", score: 45, date: todayStr }
      ];
      localStorage.setItem("ar_feed_leaderboard", JSON.stringify(mockData));
    }
  }

  function showLeaderboard() {
    const todayStr = new Date().toISOString().split('T')[0];
    const dateEl = document.getElementById("leaderboardDate");
    if (dateEl) dateEl.textContent = `今日日期：${todayStr}`;
    
    const leaderboard = JSON.parse(localStorage.getItem("ar_feed_leaderboard") || "[]");
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
    
    document.getElementById("leaderboardOverlay").classList.remove("hidden");
  }

  function setupEvents() {
    el.restartBtn.addEventListener("click", restartExperience);
    el.eventCloseBtn.addEventListener("click", closeEventModal);
    
    const showLbBtn = document.getElementById("showLeaderboardBtn");
    if (showLbBtn) {
      showLbBtn.addEventListener("click", showLeaderboard);
    }
    
    const backLbBtn = document.getElementById("leaderboardBackBtn");
    if (backLbBtn) {
      backLbBtn.addEventListener("click", () => {
        document.getElementById("leaderboardOverlay").classList.add("hidden");
      });
    }

    const startBtn = document.getElementById("startGameBtn");
    if (startBtn) {
      startBtn.addEventListener("click", () => {
        const overlay = document.getElementById("instructionsOverlay");
        if (overlay) overlay.classList.add("hidden");
        state.instructionsCleared = true;
        
        const isOnline = el.markerStatus.classList.contains("online");
        if (isOnline) {
          state.gameStarted = true;
          state.gameActive = true;
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
    setupEvents();
    setupMarkerEvents();

    state.timeRemaining = 60;
    state.growth = 0;
    state.water = { ...pondConfig.initialWater };
    state.messages = [];

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
