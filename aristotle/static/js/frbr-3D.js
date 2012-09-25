var camera, scene, renderer, 
geometry, material, mesh;

var WIDTH = 400, HEIGHT = 300;

var VIEW_ANGLE = 45, 
    ASPECT = WIDTH / HEIGHT,
	NEAR = 0.1,
	FAR = 10000;
	
init();
//animate();
render();

function init() {
  var $canvas = $('#threeDcanvas');
  renderer = new THREE.CanvasRenderer();
  scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(VIEW_ANGLE,
                                       ASPECT,
	   								   NEAR,
									   FAR);
  camera.position.z = 300;
  scene.add(camera);
  
  geometry = new THREE.CubeGeometry(150,150,150);
  material = new THREE.MeshBasicMaterial( { color: 0xff0000, wireframe: true } );
  
  mesh = new THREE.Mesh( geometry, material);
  
  scene.add(mesh);
  
  var pointLight = new THREE.PointLight( 0xFFFFFF );
  
  pointLight.position.x = 10;
  pointLight.position.y = 50;
  pointLight.position.z = 130;
  
  scene.add(pointLight);
  
  renderer.setSize(WIDTH, HEIGHT);
  $canvas.append(renderer.domElement);
 }
 
function animate() {

}

function render() {
  renderer.render(scene, camera);
}