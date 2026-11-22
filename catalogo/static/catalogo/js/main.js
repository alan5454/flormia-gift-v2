(() => {
  "use strict";
  const fmt = new Intl.NumberFormat("es-MX", { maximumFractionDigits: 2 });
  const dinero = (n) => "$" + fmt.format(n);
  const $ = (sel, raiz = document) => raiz.querySelector(sel);
  const $$ = (sel, raiz = document) => [...raiz.querySelectorAll(sel)];

  const tarjetas = $$(".tarjeta");
  const casillas = $$(".extra input");
  const boton = $("#btn-whatsapp");
  let producto = null;

  // Filtro por categoría
  $$(".pill").forEach((pill) =>
    pill.addEventListener("click", () => {
      const filtro = pill.dataset.filtro;
      $$(".pill").forEach((p) => {
        p.classList.toggle("activo", p === pill);
        p.setAttribute("aria-pressed", String(p === pill));
      });
      tarjetas.forEach((t) =>
        t.classList.toggle("oculto", filtro !== "todos" && t.dataset.categoria !== filtro)
      );
    })
  );

  // Elegir ramo o arreglo
  tarjetas.forEach((t) =>
    $(".btn-elegir", t).addEventListener("click", () => {
      producto = { nombre: t.dataset.nombre, precio: parseFloat(t.dataset.precio) || 0 };
      tarjetas.forEach((x) => {
        const activa = x === t;
        x.classList.toggle("seleccionada", activa);
        $(".btn-elegir", x).textContent = activa ? "Elegido ✓" : "Elegir";
      });
      actualizar();
    })
  );

  casillas.forEach((c) => c.addEventListener("change", actualizar));
  const mensaje = $("#mensaje");
  if (mensaje) mensaje.addEventListener("input", actualizar);

  function actualizar() {
    const extras = casillas
      .filter((c) => c.checked)
      .map((c) => ({ nombre: c.dataset.nombre, precio: parseFloat(c.dataset.precio) || 0 }));
    const total = (producto ? producto.precio : 0) + extras.reduce((s, e) => s + e.precio, 0);

    const pProducto = $("#pedido-producto");
    pProducto.textContent = producto
      ? `${producto.nombre} — ${dinero(producto.precio)}`
      : "Elige un ramo o arreglo del catálogo.";
    pProducto.classList.toggle("vacio", !producto);

    const lista = $("#pedido-extras");
    lista.replaceChildren();
    extras.forEach((e) => {
      const li = document.createElement("li");
      const a = document.createElement("span");
      const b = document.createElement("span");
      a.textContent = e.nombre;
      b.textContent = "+" + dinero(e.precio);
      li.append(a, b);
      lista.append(li);
    });

    $("#pedido-total").textContent = dinero(total);
    $("#pedido-aviso").textContent = "";

    // Mensaje de WhatsApp
    const lineas = ["¡Hola! Quisiera hacer un pedido 🌸", ""];
    if (producto) lineas.push(`• ${producto.nombre}: ${dinero(producto.precio)}`);
    if (extras.length) {
      lineas.push("• Extras:");
      extras.forEach((e) => lineas.push(`   - ${e.nombre}: ${dinero(e.precio)}`));
    }
    const nota = mensaje ? mensaje.value.trim() : "";
    if (nota) lineas.push("", `Mensaje para la tarjeta: ${nota}`);
    lineas.push("", `Total: ${dinero(total)}`);

    const numero = boton.dataset.whatsapp || "";
    boton.href = `https://wa.me/${numero}?text=${encodeURIComponent(lineas.join("\n"))}`;
    boton.setAttribute("aria-disabled", String(!producto));
  }

  boton.addEventListener("click", (ev) => {
    if (!producto) {
      ev.preventDefault();
      $("#pedido-aviso").textContent = "Primero elige un ramo o arreglo del catálogo.";
    }
  });

  actualizar();
})();
