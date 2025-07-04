import Image from "next/image";

const Header = () => {
  return (
    <header id="header" className="w-full flex self-start items-center p-[--app-padding] pb-0 justify-between">
      <div className="group flex gap-8">
        <nav className="pointer-events-none flex-row items-center gap-8 text-lg leading-7 hidden group-hover:flex group-hover:pointer-events-auto">
        </nav>
      </div>
    </header>
  );
}

export default Header;