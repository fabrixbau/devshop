from django.shortcuts import render, get_object_or_404, redirect

from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from .forms import ClienteForm

from django.core.mail import send_mail

from .models import Categoria, Producto, Cliente, Pedido, PedidoDetalle
from .carrito import Cart


from paypal.standard.forms import PayPalPaymentsForm
from django.urls import reverse

from django.http import HttpResponseNotFound
from django.template import loader

from django.conf import settings

# Create your views here.
""" VISTAS PARA EL CATALOGO DE PRODUCTOS """


def index(request):
    listaProductos = Producto.objects.all()
    listaCategorias = Categoria.objects.all()

    # print(listaProductos)

    context = {"productos": listaProductos, "categorias": listaCategorias}
    return render(request, "index.html", context)


def productosPorCategoria(request, categoria_id):
    """VISTA PARA FILTRAR PRODUCTOS POR CATEGIORIA"""
    objCategoria = Categoria.objects.get(pk=categoria_id)
    listaProductos = objCategoria.producto_set.all()

    listaCategorias = Categoria.objects.all()

    context = {"categorias": listaCategorias, "productos": listaProductos}

    return render(request, "index.html", context)


def productosPorNombre(request):
    """vistas para filtrado de productos por nombre"""
    nombre = request.POST["nombre"]

    listaProductos = Producto.objects.filter(nombre__icontains=nombre)
    listaCategorias = Categoria.objects.all()

    context = {"productos": listaProductos, "categorias": listaCategorias}
    return render(request, "index.html", context)


def productoDetalle(request, producto_id):
    """Vistas para producto y su detalle"""
    # objProducto = Producto.objects.get(pk=producto_id)
    objProducto = get_object_or_404(Producto, pk=producto_id)
    context = {"producto": objProducto}

    return render(request, "producto.html", context)


""" VISTAS PARA EL CARRITO DE COMPRAAS """


def carrito(request):
    return render(request, "carrito.html")


def agregarCarrito(request, producto_id):
    if request.method == "POST":
        cantidad = int(request.POST["cantidad"])
    else:
        cantidad = 1

    objProducto = Producto.objects.get(pk=producto_id)
    carritoProducto = Cart(request)
    carritoProducto.add(objProducto, cantidad)

    if request.method == "GET":
        return redirect("/")

    return render(request, "carrito.html")


def eliminarProductoCarrito(request, producto_id):
    objProducto = Producto.objects.get(pk=producto_id)
    carritoProducto = Cart(request)
    carritoProducto.delete(objProducto)

    return render(request, "carrito.html")


def limpiarCarrito(request):
    carritoProducto = Cart(request)
    carritoProducto.clear()

    return render(request, "carrito.html")


""" VISTAS PARA CLIENTES Y USUARIOS """


def crearUsuario(request):
    if request.method == "POST":
        dataUsuario = request.POST["nuevoUsuario"]
        dataPassword = request.POST["nuevoPassword"]

        nuevoUsuario = User.objects.create_user(
            username=dataUsuario, password=dataPassword
        )
        if nuevoUsuario is not None:
            login(request, nuevoUsuario)
            return redirect("/cuenta")

    return render(request, "login.html")


def loginUsuario(request):
    paginaDestino = request.GET.get("next", None)
    context = {"destino": paginaDestino}

    if request.method == "POST":
        dataUsuario = request.POST["usuario"]
        dataPassword = request.POST["password"]
        dataDestino = request.POST["destino"]

        usuarioAuth = authenticate(request, username=dataUsuario,
                                   password=dataPassword)
        if usuarioAuth is not None:
            login(request, usuarioAuth)

            if dataDestino != "None":
                return redirect('/cuenta')

            return redirect("/cuenta")
        else:
            context = {"mensajeError": "Datos incorrectos"}

    return render(request, "login.html", context)


def logoutUsuario(request):
    logout(request)
    return render(request, "login.html")


def cuentaUsuario(request):
    try:
        clienteEditar = Cliente.objects.get(usuario=request.user)

        dataCliente = {
            "nombre": request.user.first_name,
            "apellidos": request.user.last_name,
            "email": request.user.email,
            "direccion": clienteEditar.direccion,
            "telefono": clienteEditar.telefono,
            "dni": clienteEditar.dni,
            "sexo": clienteEditar.sexo,
            "fecha_nacimiento": clienteEditar.fecha_nacimiento,
        }
    except Cliente.DoesNotExist:
        dataCliente = {
            "nombre": request.user.first_name,
            "apellidos": request.user.last_name,
            "email": request.user.email,
        }

    frmCliente = ClienteForm(dataCliente)
    context = {"frmCliente": frmCliente}

    return render(request, "cuenta.html", context)


def actualizarCliente(request):
    mensaje = ""

    if request.method == "POST":
        frmCliente = ClienteForm(request.POST)
        if frmCliente.is_valid():
            dataCliente = frmCliente.cleaned_data

            # actualizar usuario
            actUsuario = User.objects.get(pk=request.user.id)
            actUsuario.first_name = dataCliente["nombre"]
            actUsuario.last_name = dataCliente["apellidos"]
            actUsuario.email = dataCliente["email"]
            actUsuario.save()

            # registrar cliente
            nuevoCliente = Cliente()
            nuevoCliente.usuario = actUsuario
            nuevoCliente.dni = dataCliente["dni"]
            nuevoCliente.direccion = dataCliente["direccion"]
            nuevoCliente.telefono = dataCliente["telefono"]
            nuevoCliente.sexo = dataCliente["sexo"]
            nuevoCliente.fecha_nacimiento = dataCliente["fecha_nacimiento"]
            nuevoCliente.save()

            mensaje = "Datos actualizados correctamente"

    context = {"mensaje": mensaje, "frmCliente": frmCliente}

    return render(request, "cuenta.html", context)


""" VISTAS PARA PROCESO DE COMPRA """

# VISTAS PRUEBA DE PAYPAL


def view_that_asks_for_money(request):

    # What you want the button to do.
    paypal_dict = {
        "business": settings.PAYPAL_USER_EMAIL,
        "amount": "100.00",
        "item_name": "Producto prueba edteam",
        "invoice": "100-developershop",
        "notify_url": request.build_absolute_uri(reverse("paypal-ipn")),
        "return": request.build_absolute_uri(("/")),
        "cancel_return": request.build_absolute_uri(("/logout")),
        # Custom command to correlate to some function later (optional)
        "custom": "premium_plan",
    }

    # Create the instance.
    form = PayPalPaymentsForm(initial=paypal_dict)
    context = {"form": form}
    return render(request, "payment.html", context)


@login_required(login_url="/login")
def registrarPedido(request):
    try:
        clienteEditar = Cliente.objects.get(usuario=request.user)

        dataCliente = {
            "nombre": request.user.first_name,
            "apellidos": request.user.last_name,
            "email": request.user.email,
            "direccion": clienteEditar.direccion,
            "telefono": clienteEditar.telefono,
            "dni": clienteEditar.dni,
            "sexo": clienteEditar.sexo,
            "fecha_nacimiento": clienteEditar.fecha_nacimiento,
        }
    except Cliente.DoesNotExist:
        dataCliente = {
            "nombre": request.user.first_name,
            "apellidos": request.user.last_name,
            "email": request.user.email,
        }

    frmCliente = ClienteForm(dataCliente)
    context = {"frmCliente": frmCliente}

    return render(request, "pedido.html", context)


@login_required(login_url="/login")
def confirmarPedido(request):
    context = {}
    if request.method == "POST":
        # actualizamos datos de usuario
        actUsuario = User.objects.get(pk=request.user.id)
        actUsuario.first_name = request.POST["nombre"]
        actUsuario.last_name = request.POST["apellidos"]
        actUsuario.save()

        # registramos o actualizamos cliente
        try:
            clientePedido = Cliente.objects.get(usuario=request.user)
            clientePedido.telefono = request.POST["telefono"]
            clientePedido.direccion = request.POST["direccion"]
            clientePedido.save()
        except clientePedido.DoesNotExist:
            clientePedido = Cliente()
            clientePedido.usuario = actUsuario
            clientePedido.direccion = request.POST["direccion"]
            clientePedido.telefono = request.POST["telefono"]
            clientePedido.save()

        # registramos nuevo pedido
        nroPedido = ""
        montoTotal = float(request.session.get("cartMontoTotal"))
        nuevoPedido = Pedido()
        nuevoPedido.cliente = clientePedido
        nuevoPedido.save()

        # registramos el detalle de pedido
        carritoPedido = request.session.get("cart")
        for key, value in carritoPedido.items():
            productoPedido = Producto.objects.get(pk=value["producto_id"])
            detalle = PedidoDetalle()
            detalle.pedido = nuevoPedido
            detalle.producto = productoPedido
            detalle.cantidad = int(value["cantidad"])
            detalle.subtotal = float(value["subtotal"])
            detalle.save()

        # actualizar el pedido
        nroPedido = (
            "PED" +
            nuevoPedido.fecha_registro.strftime("%Y") + str(nuevoPedido.id)
        )
        nuevoPedido.nro_pedido = nroPedido
        nuevoPedido.monto_total = montoTotal
        nuevoPedido.save()

        # registrar variable de sesion para el pedido
        request.session["pedidoId"] = nuevoPedido.id

        # creamos boton de paypal
        paypal_dict = {
            "business": settings.PAYPAL_USER_EMAIL,
            "amount": montoTotal,
            "item_name": "PEDIDO CODIGO : " + nroPedido,
            "invoice": nroPedido,
            "notify_url": request.build_absolute_uri(reverse("paypal-ipn")),
            "return": request.build_absolute_uri(("/gracias")),
            "cancel_return": request.build_absolute_uri(("/")),
        }

        # Create the instance.
        formPaypal = PayPalPaymentsForm(initial=paypal_dict)

        context = {"pedido": nuevoPedido, "formPaypal": formPaypal}

        # limpiamos carrito de compras
        carrito = Cart(request)
        carrito.clear()
    return render(request, "compra.html", context)


@login_required(login_url="/login")
def gracias(request):
    paypalId = request.GET.get("PayerID", None)
    context = {}

    if paypalId is not None:
        pedidoId = request.session.get("pedidoId")
        pedido = Pedido.objects.get(pk=pedidoId)
        pedido.estado = "1"
        pedido.save()

        send_mail(
            "Gracias por tu compra",
            "Tu numero de pedido es " + pedido.nro_pedido,
            settings.ADMIN_USER_EMAIL,
            [request.user.email],
            fail_silently=False,
        )
        context = {"pedido": pedido}
    else:
        return redirect("/")

    return render(request, "gracias.html", context)


""" VISTAS PARA MANEJAR LOS ERORRES """


def my_custom_page_not_found_view(request, exception):
    template = loader.get_template("404.html")
    return HttpResponseNotFound(template.render({}, request))


""" VISTAS PARA ADMIN Y PEDIDOS """


@login_required
def lista_pedidos(request):
    if request.user.is_superuser:
        pedidos = Pedido.objects.all().order_by('-fecha_registro')
        return render(request, 'lista_pedidos.html', {'pedidos': pedidos})
    else:
        return redirect('/')


@login_required
def detalle_pedido(request, pedido_id):
    if request.user.is_superuser:
        pedido = get_object_or_404(Pedido, id=pedido_id)
        detalles = PedidoDetalle.objects.filter(pedido=pedido)
        return render(request, 'detalle_pedido.html', {'pedido': pedido,
                                                       'detalles': detalles})
    else:
        return redirect('/')
