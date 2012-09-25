display();

function display() {
 var c = document.getElementById('threeDcanvas');
 var ctx = c.getContext("2d");
 ctx.fillStyle = rgb(255,242,204);
 ctx.fillRect(20,20,150,150);

}