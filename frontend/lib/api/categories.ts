import { apiClient } from "@/lib/api/client";
import type { ApiSuccess } from "@/types/api";
import type { CategoryRead } from "@/types/catalog";

/**
 * GET uniquement — aucune route POST/PUT/DELETE exposée pour cette
 * ressource (écart documenté : CategoryCreate/Update existent dans les
 * schemas backend mais le router n'expose pas de CRUD). Ne pas ajouter
 * de fonction create/update/delete ici sans nouvelle décision.
 */
export const categoriesApi = {
  list: () => apiClient.get<ApiSuccess<CategoryRead[]>>("/api/v1/categories"),
};
