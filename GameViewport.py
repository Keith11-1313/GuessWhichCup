"""Scale one logical game canvas, including images, text and mouse input.

Turtle and the UI keep their existing logical coordinates. This adapter wraps
public Tk canvas methods so fullscreen rendering uses the available display.
Pillow supplies cached nearest-neighbor image scaling; no screenshots are used.
"""

from NamingCompatibility import ReadAttribute, WriteAttribute

import io as Io
import tkinter as Tk
from tkinter import font as Font
from PIL import Image as PillowImage
from GameObjects import InputCanvas
from GameConfig import Width, Height


class GameViewport:
    def __init__(Self, Session):
        Self.Session = Session
        Self.Canvas = Session.Screen.getcanvas()
        Self.Widget = InputCanvas(Session.Screen)
        Self.Factor = 1.0
        Self.Metadata = {}
        Self.Images = {}
        Self.ScaledImages = {}
        Self.Fonts = {}
        Self.BackdropKey = None
        Self.BackdropCache = {}
        Names = (
            "coords",
            "move",
            "scale",
            "bbox",
            "canvasx",
            "canvasy",
            "delete",
            "itemconfigure",
            "itemconfig",
            "create_image",
            "create_text",
            "create_rectangle",
            "create_line",
            "create_polygon",
            "create_oval",
        )
        Self.Raw = {Name: ReadAttribute(Self.Widget, Name) for Name in Names}
        Self.CollectImages(Session.Assets)
        for Name in Names:
            Wrapper = ReadAttribute(Self, Name)
            WriteAttribute(Self.Widget, Name, Wrapper)
            WriteAttribute(Self.Canvas, Name, Wrapper)
        Self.Widget.bind("<Configure>", lambda Event: Self.Resize(), add="+")

    def CollectImages(Self, Value):
        if isinstance(Value, Tk.PhotoImage):
            Self.Images[str(Value)] = Value
        elif isinstance(Value, dict):
            for Child in Value.values():
                Self.CollectImages(Child)
        elif isinstance(Value, (list, tuple)):
            for Child in Value:
                Self.CollectImages(Child)

    def ScaledImage(Self, Value):
        if not Value or Self.Factor == 1:
            return Value
        Name = str(Value)
        if Name not in Self.Images:
            return Value
        Key = (Name, Self.Factor)
        if Key not in Self.ScaledImages:
            Source = Self.Images[Name]
            Data = Source.tk.call(Name, "data", "-format", "png")
            Image = PillowImage.open(Io.BytesIO(Data)).convert("RGBA")
            Image = Image.resize(
                (
                    max(1, round(Image.width * Self.Factor)),
                    max(1, round(Image.height * Self.Factor)),
                ),
                PillowImage.Resampling.NEAREST,
            )
            Buffer = Io.BytesIO()
            Image.save(Buffer, format="PNG")
            Self.ScaledImages[Key] = Tk.PhotoImage(
                data=Buffer.getvalue(), master=Self.Widget
            )
        return Self.ScaledImages[Key]

    def ScaledFont(Self, Value):
        if Self.Factor == 1:
            return Value
        Key = (str(Value), Self.Factor)
        if Key not in Self.Fonts:
            Style = Font.Font(root=Self.Widget, font=Value).actual()
            Style["size"] = round(Style["size"] * Self.Factor)
            Self.Fonts[Key] = Font.Font(root=Self.Widget, **Style)
        return Self.Fonts[Key]

    def Points(Self, Values):
        return tuple(
            Self.Points(V) if isinstance(V, (list, tuple)) else V * Self.Factor
            for V in Values
        )

    def Attributes(Self, Item, Values):
        Values = dict(Values)
        Saved = Self.Metadata.setdefault(Item, {})
        for Key in ("image", "font", "width"):
            if Key in Values:
                Saved[Key] = Values[Key]
                if Key == "image":
                    Values[Key] = Self.ScaledImage(Values[Key])
                elif Key == "font":
                    Values[Key] = Self.ScaledFont(Values[Key])
                elif isinstance(Values[Key], (int, float)):
                    Values[Key] *= Self.Factor
        return Values

    def Create(Self, Kind, Coordinates, Values):
        Item = Self.Raw[Kind](*Self.Points(Coordinates), **Self.Attributes(0, Values))
        Self.Metadata[Item] = Self.Metadata.pop(0, {})
        return Item

    def CreateImage(Self, *Args, **Kwargs):
        return Self.Create("create_image", Args, Kwargs)

    def CreateText(Self, *Args, **Kwargs):
        return Self.Create("create_text", Args, Kwargs)

    def CreateRectangle(Self, *Args, **Kwargs):
        return Self.Create("create_rectangle", Args, Kwargs)

    def CreateLine(Self, *Args, **Kwargs):
        return Self.Create("create_line", Args, Kwargs)

    def CreatePolygon(Self, *Args, **Kwargs):
        return Self.Create("create_polygon", Args, Kwargs)

    def CreateOval(Self, *Args, **Kwargs):
        return Self.Create("create_oval", Args, Kwargs)

    def Coords(Self, Item, *Coordinates):
        if Coordinates:
            return Self.Raw["coords"](Item, *Self.Points(Coordinates))
        return [Value / Self.Factor for Value in Self.Raw["coords"](Item)]

    def Move(Self, Item, X, Y):
        return Self.Raw["move"](Item, X * Self.Factor, Y * Self.Factor)

    def Scale(Self, Item, X, Y, Sx, Sy):
        return Self.Raw["scale"](Item, X * Self.Factor, Y * Self.Factor, Sx, Sy)

    def Bbox(Self, *Items):
        Result = Self.Raw["bbox"](*Items)
        return tuple(Value / Self.Factor for Value in Result) if Result else None

    def Canvasx(Self, Value, *Args):
        return Self.Raw["canvasx"](Value, *Args) / Self.Factor

    def Canvasy(Self, Value, *Args):
        return Self.Raw["canvasy"](Value, *Args) / Self.Factor

    def Itemconfigure(Self, Item, Cnf=None, **Kwargs):
        if isinstance(Cnf, dict):
            Kwargs = dict(Cnf, **Kwargs)
        if Kwargs:
            return Self.Raw["itemconfigure"](Item, **Self.Attributes(Item, Kwargs))
        return Self.Raw["itemconfigure"](Item, Cnf)

    Itemconfig = Itemconfigure

    def Delete(Self, *Items):
        for Tag in Items:
            for Item in Self.Widget.find_withtag(Tag):
                Self.Metadata.pop(Item, None)
        return Self.Raw["delete"](*Items)

    def Resize(Self):
        if Self.Widget.winfo_width() < 200:
            return
        Target = (
            min(Self.Widget.winfo_width() / Width, Self.Widget.winfo_height() / Height)
            if Self.Session.Settings.Values["fullscreen"]
            else 1.0
        )
        Target = round(Target, 3)
        if abs(Target - Self.Factor) < 0.005:
            return
        Ratio = Target / Self.Factor
        Self.Factor = Target
        Self.Raw["scale"]("all", 0, 0, Ratio, Ratio)
        for Item in Self.Widget.find_all():
            Values = Self.Metadata.get(Item, {})
            if Values:
                Self.Raw["itemconfigure"](Item, **Self.Attributes(Item, Values))
        Self.BackdropKey = None
        Self.RefreshBackdrop()

    def RefreshBackdrop(Self):
        if not Self.Session.Settings.Values["fullscreen"]:
            Self.Raw["delete"]("viewport_backdrop")
            Self.BackdropKey = None
            return
        from PIL import ImageOps, ImageEnhance

        Name = ReadAttribute(Self.Session, "scene_location", "hall")
        Size = (Self.Widget.winfo_width(), Self.Widget.winfo_height())
        Key = (Name, Size)
        if Self.BackdropKey == Key:
            return
        if Key not in Self.BackdropCache:
            Source = Self.Session.Assets["backgrounds"][Name]
            Data = Source.tk.call(str(Source), "data", "-format", "png")
            Image = PillowImage.open(Io.BytesIO(Data)).convert("RGB")
            Image = ImageOps.fit(Image, Size, method=PillowImage.Resampling.NEAREST)
            Image = ImageEnhance.Brightness(Image).enhance(0.25)
            Buffer = Io.BytesIO()
            Image.save(Buffer, format="PNG")
            Self.BackdropCache[Key] = Tk.PhotoImage(
                data=Buffer.getvalue(), master=Self.Widget
            )
        Self.Raw["delete"]("viewport_backdrop")
        Self.BackdropKey = Key
        Self.Backdrop = Self.BackdropCache[Key]
        Item = Self.Raw["create_image"](
            0, 0, image=Self.Backdrop, tags=("viewport_backdrop",)
        )
        Self.Widget.tag_lower(Item)
