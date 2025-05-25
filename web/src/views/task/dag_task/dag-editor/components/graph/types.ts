export interface MenuItem {
  img: any;
  id: string | number;
  name: string;
  params: object;
}

export interface MenuGroup {
  title: string;
  name: string;
  children?: MenuItem[];
}

export interface MenuData {
  groups: MenuGroup[];
  items: any;
}
