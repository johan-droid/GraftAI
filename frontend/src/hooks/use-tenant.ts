"use client";

import { useState, useEffect, useCallback } from "react";
import { 
  getActiveOrgId, 
  getActiveWorkspaceId, 
  listMyOrganizations, 
  listWorkspaces,
  Organization, 
  Workspace 
} from "@/lib/api";

export function useTenant() {
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [activeOrgId, setActiveOrgId] = useState<string | null>(null);
  const [activeWorkspaceId, setActiveWorkspaceId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isWorkspacesLoading, setIsWorkspacesLoading] = useState(false);

  const fetchOrgs = useCallback(async () => {
    try {
      setIsLoading(true);
      const orgs = await listMyOrganizations();
      setOrganizations(orgs);
      
      const savedOrgId = getActiveOrgId();
      const savedWorkspaceId = getActiveWorkspaceId();

      if (savedOrgId && orgs.find(o => o.id.toString() === savedOrgId)) {
        setActiveOrgId(savedOrgId);
        setActiveWorkspaceId(savedWorkspaceId);
      } else if (orgs.length > 0) {
        // Auto-select first org if none saved or saved is invalid
        const firstOrg = orgs[0];
        localStorage.setItem("graftai_org_id", firstOrg.id.toString());
        setActiveOrgId(firstOrg.id.toString());
      }
    } catch (error) {
      console.error("Failed to fetch organizations:", error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const fetchWorkspacesData = useCallback(async (orgId: string) => {
    try {
      setIsWorkspacesLoading(true);
      const data = await listWorkspaces(parseInt(orgId));
      setWorkspaces(data);
    } catch (error) {
      console.error("Failed to fetch workspaces:", error);
      setWorkspaces([]);
    } finally {
      setIsWorkspacesLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchOrgs();
  }, [fetchOrgs]);

  useEffect(() => {
    if (activeOrgId) {
      fetchWorkspacesData(activeOrgId);
    } else {
      setWorkspaces([]);
    }
  }, [activeOrgId, fetchWorkspacesData]);

  const switchOrganization = (orgId: string, workspaceId?: string) => {
    localStorage.setItem("graftai_org_id", orgId);
    if (workspaceId) {
      localStorage.setItem("graftai_workspace_id", workspaceId);
    } else {
      localStorage.removeItem("graftai_workspace_id"); // Clear workspace if switching org
    }
    // Hard refresh to reset all API headers and clear context
    window.location.reload();
  };

  const switchWorkspace = (workspaceId: string) => {
    if (!activeOrgId) return;
    localStorage.setItem("graftai_workspace_id", workspaceId);
    window.location.reload();
  };

  return {
    organizations,
    workspaces,
    activeOrgId,
    activeWorkspaceId,
    isLoading,
    isWorkspacesLoading,
    switchOrganization,
    switchWorkspace,
    refreshOrgs: fetchOrgs
  };
}
