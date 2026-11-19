import * as THREE from 'three';

export async function mountCampusScene(canvas) {
  if (!canvas) return;
  const host = canvas.parentElement;
  const width = Math.max(1, host.clientWidth);
  const height = Math.max(1, host.clientHeight);
  let renderer;
  let renderCanvas = canvas;

  // Prefer the next-generation WebGPU renderer, then gracefully fall back to WebGL 2.
  try {
    const { WebGPURenderer } = await import('three/webgpu');
    const candidate = new WebGPURenderer({ canvas: renderCanvas, alpha: true, antialias: true, powerPreference: 'high-performance' });
    candidate.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.7));
    candidate.setSize(width, height, false);
    await candidate.init();
    renderer = candidate;
  } catch (webgpuError) {
    // Replace the canvas before asking for WebGL: a failed WebGPU init may already
    // have attached a context to the original canvas, and canvases cannot swap APIs.
    const replacement = renderCanvas.cloneNode(false);
    renderCanvas.replaceWith(replacement);
    renderCanvas = replacement;
    renderer = new THREE.WebGLRenderer({ canvas: renderCanvas, alpha: true, antialias: true, powerPreference: 'high-performance' });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.7));
    renderer.setSize(width, height, false);
  }

  renderer.setClearColor(0x000000, 0);
  if ('outputColorSpace' in renderer) renderer.outputColorSpace = THREE.SRGBColorSpace;
  if ('toneMapping' in renderer) renderer.toneMapping = THREE.ACESFilmicToneMapping;
  if ('toneMappingExposure' in renderer) renderer.toneMappingExposure = 1.18;

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(33, width / height, 0.1, 80);
  camera.position.set(0, 2.25, 8.3);
  const group = new THREE.Group();
  scene.add(group);

  scene.add(new THREE.HemisphereLight(0xc6d7ff, 0x17203b, 2.15));
  const key = new THREE.DirectionalLight(0xb9b4ff, 3.2); key.position.set(-4, 6, 5); scene.add(key);
  const cyanLight = new THREE.PointLight(0x43dce9, 26, 15); cyanLight.position.set(3, 1, 2); scene.add(cyanLight);
  const violetLight = new THREE.PointLight(0x8b70ff, 33, 16); violetLight.position.set(-3, 2, -1); scene.add(violetLight);

  const glass = new THREE.MeshPhysicalMaterial({ color: 0x625ce9, metalness: 0.42, roughness: 0.2, transmission: 0.14, thickness: 0.8, clearcoat: 1, clearcoatRoughness: 0.12, transparent: true, opacity: 0.9 });
  const pale = new THREE.MeshPhysicalMaterial({ color: 0xd9e6ff, metalness: 0.5, roughness: 0.23, clearcoat: 1 });
  const cyan = new THREE.MeshStandardMaterial({ color: 0x63e4eb, metalness: 0.68, roughness: 0.2, emissive: 0x1b9aaa, emissiveIntensity: 0.7 });
  const darkGlass = new THREE.MeshPhysicalMaterial({ color: 0x202f66, metalness: 0.48, roughness: 0.24, clearcoat: 1, transparent: true, opacity: 0.92 });

  const floor = new THREE.Mesh(new THREE.CylinderGeometry(2.5, 2.7, 0.12, 80), new THREE.MeshStandardMaterial({ color: 0x29346b, metalness: 0.74, roughness: 0.3 }));
  floor.position.y = -1.18; floor.receiveShadow = true; group.add(floor);
  const floorRing = new THREE.Mesh(new THREE.TorusGeometry(2.42, 0.018, 10, 120), cyan); floorRing.rotation.x = Math.PI / 2; floorRing.position.y = -1.1; group.add(floorRing);

  // A small stylized campus: podiums, three wings, pitched roofs and luminous windows.
  const podium = new THREE.Mesh(new THREE.BoxGeometry(2.65, 0.18, 1.8), darkGlass); podium.position.set(0, -1.02, 0); group.add(podium);
  const building = new THREE.Group(); group.add(building);
  const wingData = [
    {x:-0.83,y:-0.28,z:0.03,w:0.72,h:1.35,d:0.92,mat:glass},
    {x:0,y:-0.08,z:0.03,w:0.82,h:1.72,d:1.05,mat:pale},
    {x:0.84,y:-0.38,z:0.03,w:0.7,h:1.18,d:0.88,mat:darkGlass}
  ];
  wingData.forEach((item,index)=>{
    const block = new THREE.Mesh(new THREE.BoxGeometry(item.w,item.h,item.d),item.mat);
    block.position.set(item.x,item.y,item.z); building.add(block);
    const roof = new THREE.Mesh(new THREE.ConeGeometry(item.w*0.76,0.34,4), index===1?cyan:glass);
    roof.position.set(item.x,item.y+item.h/2+0.14,item.z); roof.rotation.y=Math.PI/4; building.add(roof);
    const cols = index===1?3:2;
    for(let row=0;row<3;row++) for(let col=0;col<cols;col++){
      const windowMesh=new THREE.Mesh(new THREE.BoxGeometry(0.1,0.15,0.018),new THREE.MeshStandardMaterial({color:0x9feaf2,emissive:0x3ebdce,emissiveIntensity:1.4,metalness:.25,roughness:.2}));
      windowMesh.position.set(item.x+(col-(cols-1)/2)*(item.w/(cols+0.45)),item.y+0.25-row*.34,item.z+item.d/2+0.014);building.add(windowMesh);
    }
  });
  const steps = new THREE.Mesh(new THREE.BoxGeometry(1.05,0.15,0.4),pale);steps.position.set(0,-0.95,0.87);building.add(steps);
  const door = new THREE.Mesh(new THREE.BoxGeometry(.23,.56,.04),darkGlass);door.position.set(0,-.68,.57);building.add(door);

  const haloGroup = new THREE.Group(); group.add(haloGroup);
  [[2.15,0.025,0x9a8aff,0.15],[2.45,0.012,0x5ee1e7,-0.35],[1.88,0.012,0x8cb1ff,0.72]].forEach(([r,t,c,rot])=>{
    const ring=new THREE.Mesh(new THREE.TorusGeometry(r,t,12,140),new THREE.MeshStandardMaterial({color:c,metalness:.75,roughness:.18,emissive:c,emissiveIntensity:.28}));ring.rotation.x=1.08+rot*.23;ring.rotation.y=rot*.18;haloGroup.add(ring);
  });
  const crystal = new THREE.Mesh(new THREE.IcosahedronGeometry(0.38,1),new THREE.MeshPhysicalMaterial({color:0x8bdce8,metalness:.25,roughness:.08,transmission:.72,thickness:1.4,clearcoat:1,emissive:0x3248a3,emissiveIntensity:.18}));
  crystal.position.set(0,1.65,-.1); group.add(crystal);
  const crystalWire=new THREE.Mesh(new THREE.IcosahedronGeometry(.43,1),new THREE.MeshBasicMaterial({color:0xb9a9ff,wireframe:true,transparent:true,opacity:.34}));crystalWire.position.copy(crystal.position);group.add(crystalWire);

  const starsGeometry = new THREE.BufferGeometry();
  const starPositions = new Float32Array(450*3);
  for(let i=0;i<450;i++){
    const radius=2.2+Math.random()*4.1;const angle=Math.random()*Math.PI*2;
    starPositions[i*3]=Math.cos(angle)*radius;
    starPositions[i*3+1]=(Math.random()-.5)*4.2;
    starPositions[i*3+2]=(Math.sin(angle)*radius)-.5;
  }
  starsGeometry.setAttribute('position',new THREE.BufferAttribute(starPositions,3));
  const stars=new THREE.Points(starsGeometry,new THREE.PointsMaterial({color:0x9aa7ff,size:.018,transparent:true,opacity:.75,sizeAttenuation:true}));scene.add(stars);

  const pointer={x:0,y:0};
  host.addEventListener('pointermove',event=>{
    const rect=host.getBoundingClientRect();pointer.x=(event.clientX-rect.left)/rect.width-.5;pointer.y=(event.clientY-rect.top)/rect.height-.5;
  },{passive:true});
  host.addEventListener('pointerleave',()=>{pointer.x=0;pointer.y=0;},{passive:true});
  const resizeObserver = new ResizeObserver(entries=>{
    const rect=entries[0].contentRect;const w=Math.max(1,rect.width),h=Math.max(1,rect.height);
    camera.aspect=w/h;camera.updateProjectionMatrix();renderer.setSize(w,h,false);
  });
  resizeObserver.observe(host);
  const reduce=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  renderer.setAnimationLoop((time)=>{
    const t=time*.001;
    if(!reduce){
      building.rotation.y=Math.sin(t*.22)*.1;
      haloGroup.rotation.y=t*.105;
      haloGroup.rotation.z=Math.sin(t*.18)*.06;
      crystal.rotation.x=t*.22;crystal.rotation.y=t*.38;
      crystalWire.rotation.copy(crystal.rotation);
      group.rotation.y+=(pointer.x*.11-group.rotation.y)*.025;
      group.rotation.x+=(-pointer.y*.06-group.rotation.x)*.025;
      stars.rotation.y=t*.012;
    }
    renderer.render(scene,camera);
  });
  return {renderer,scene,camera,dispose(){resizeObserver.disconnect();renderer.setAnimationLoop(null);renderer.dispose();}};
}
