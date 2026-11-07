import { MenuIcon } from "lucide-react";
import { Link } from "react-router";
import { Button } from "./ui/button";
import { NavigationMenu, NavigationMenuItem, NavigationMenuLink, NavigationMenuList, navigationMenuTriggerStyle } from "./ui/navigation-menu";
import { Separator } from "./ui/separator";
import { Sheet, SheetClose, SheetContent, SheetHeader, SheetTrigger } from "./ui/sheet";

// Same top-bar pattern as the owner's original navigation (fixed bar, NavigationMenu on desktop, Sheet on mobile); the menu is the Pascal workflow.
const menus = [{ name: "Projects", to: "/projects" }];

export default function Navigation() {
  return (
    <nav className="fixed left-0 right-0 top-0 z-50 flex h-16 items-center justify-between bg-background/50 px-5 shadow-xs backdrop-blur md:px-20">
      <div className="flex h-full items-center">
        <Link to="/" className="text-lg font-extrabold tracking-tighter">Pascal</Link>
        <Separator orientation="vertical" className="mx-4 h-6" />
        <NavigationMenu className="hidden md:block">
          <NavigationMenuList>
            {menus.map((m) => (
              <NavigationMenuItem key={m.name}>
                <NavigationMenuLink asChild className={navigationMenuTriggerStyle()}>
                  <Link to={m.to}>{m.name}</Link>
                </NavigationMenuLink>
              </NavigationMenuItem>
            ))}
          </NavigationMenuList>
        </NavigationMenu>
        <span className="ml-3 hidden text-sm text-muted-foreground md:inline">portfolio workbench</span>
      </div>
      <Sheet>
        <SheetTrigger asChild className="md:hidden">
          <Button variant="ghost" size="icon" aria-label="menu">
            <MenuIcon className="size-6" />
          </Button>
        </SheetTrigger>
        <SheetContent side="left">
          <SheetHeader />
          <nav className="mt-6 flex flex-col gap-2">
            {menus.map((m) => (
              <SheetClose asChild key={m.name}>
                <Link to={m.to} className="rounded-md px-3 py-2 hover:bg-accent">{m.name}</Link>
              </SheetClose>
            ))}
          </nav>
        </SheetContent>
      </Sheet>
    </nav>
  );
}
