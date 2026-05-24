"use server";

import { backendFetch, handleApiResponse } from "../../../lib/api";

export interface Category {
  id: string;
  name: string;
  display_order: number;
}

export interface MenuItem {
  id: string;
  name: string;
  price: number;
  status: string;
  category_id: string;
  station_code: string;
}

/**
 * Server Action to fetch all menu categories for the current tenant.
 */
export async function getCategoriesAction(): Promise<Category[]> {
  const response = await backendFetch("/api/internal/menu/categories", {
    method: "GET",
    permissions: "tenant.menu.manage",
    next: { revalidate: 0 }
  });
  return handleApiResponse<Category[]>(response);
}

/**
 * Server Action to fetch all menu items for the current tenant.
 */
export async function getMenuItemsAction(): Promise<MenuItem[]> {
  const response = await backendFetch("/api/internal/menu/items", {
    method: "GET",
    permissions: "tenant.menu.manage",
    next: { revalidate: 0 }
  });
  return handleApiResponse<MenuItem[]>(response);
}

/**
 * Server Action to create a new menu category.
 */
export async function createCategoryAction(name: string, displayOrder: number): Promise<Category> {
  const response = await backendFetch("/api/internal/menu/categories", {
    method: "POST",
    permissions: "tenant.menu.manage",
    body: JSON.stringify({
      name,
      display_order: displayOrder
    })
  });
  return handleApiResponse<Category>(response);
}

/**
 * Server Action to update an existing menu category.
 */
export async function updateCategoryAction(id: string, name: string, displayOrder: number): Promise<Category> {
  const response = await backendFetch(`/api/internal/menu/categories/${id}`, {
    method: "PUT",
    permissions: "tenant.menu.manage",
    body: JSON.stringify({
      name,
      display_order: displayOrder
    })
  });
  return handleApiResponse<Category>(response);
}

/**
 * Server Action to delete a menu category.
 */
export async function deleteCategoryAction(id: string): Promise<{ status: string; message: string }> {
  const response = await backendFetch(`/api/internal/menu/categories/${id}`, {
    method: "DELETE",
    permissions: "tenant.menu.manage"
  });
  return handleApiResponse<{ status: string; message: string }>(response);
}

/**
 * Server Action to create a new menu item.
 */
export async function createMenuItemAction(
  name: string,
  price: number,
  categoryId: string,
  stationCode: string
): Promise<MenuItem> {
  const response = await backendFetch("/api/internal/menu/items", {
    method: "POST",
    permissions: "tenant.menu.manage",
    body: JSON.stringify({
      name,
      price,
      category_id: categoryId,
      station_code: stationCode
    })
  });
  return handleApiResponse<MenuItem>(response);
}

/**
 * Server Action to update an existing menu item.
 */
export async function updateMenuItemAction(
  id: string,
  name: string,
  price: number,
  categoryId: string,
  stationCode: string,
  status: string
): Promise<MenuItem> {
  const response = await backendFetch(`/api/internal/menu/items/${id}`, {
    method: "PUT",
    permissions: "tenant.menu.manage",
    body: JSON.stringify({
      name,
      price,
      category_id: categoryId,
      station_code: stationCode,
      status
    })
  });
  return handleApiResponse<MenuItem>(response);
}

/**
 * Server Action to delete a menu item.
 */
export async function deleteMenuItemAction(id: string): Promise<{ status: string; message: string }> {
  const response = await backendFetch(`/api/internal/menu/items/${id}`, {
    method: "DELETE",
    permissions: "tenant.menu.manage"
  });
  return handleApiResponse<{ status: string; message: string }>(response);
}
