"use client";

import * as React from "react";
import Link from "next/link";
import { User as UserType } from "@/types";
import { ShieldAlert, LogOut, User, Package } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@radix-ui/react-dropdown-menu";

interface ShopUserMenuProps {
  user: UserType;
  isAdmin: boolean;
  onLogout: () => Promise<void>;
}

export function ShopUserMenu({ user, isAdmin, onLogout }: ShopUserMenuProps) {
  return (
    <div className="flex items-center gap-2">
      {isAdmin && (
        <Link href="/admin">
          <Badge
            variant="destructive"
            className="hidden xl:inline-flex items-center gap-1 cursor-pointer bg-red-500/20 text-red-500 dark:text-red-400 border border-red-500/30 hover:bg-red-500/30 text-[10px]"
          >
            <ShieldAlert className="h-3 w-3" />
            ADMIN
          </Badge>
        </Link>
      )}

      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            variant="ghost"
            className="relative h-9 w-9 sm:h-10 sm:w-10 rounded-full p-0 ring-1 ring-border cursor-pointer"
          >
            <Avatar className="h-8 w-8 sm:h-9 sm:w-9">
              <AvatarImage
                src={user.avatar_url || ""}
                alt={user.full_name || user.email}
              />
              <AvatarFallback className="bg-primary/10 text-primary font-semibold text-xs">
                {(user.full_name || user.email).charAt(0).toUpperCase()}
              </AvatarFallback>
            </Avatar>
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent
          className="w-56 mt-2 z-50 rounded-xl border border-border bg-popover p-2 text-popover-foreground shadow-2xl backdrop-blur-xl"
          align="end"
        >
          <DropdownMenuLabel className="px-2 py-1.5 text-xs">
            <p className="font-semibold text-foreground truncate">
              {user.full_name || "Người dùng"}
            </p>
            <p className="text-[11px] text-muted-foreground truncate">
              {user.email}
            </p>
          </DropdownMenuLabel>
          <DropdownMenuSeparator className="my-1 h-px bg-border" />
          <DropdownMenuItem
            className="flex items-center gap-2 rounded-lg px-2 py-1.5 text-xs text-foreground hover:bg-muted cursor-pointer"
            asChild
          >
            <Link href="/profile">
              <User className="h-3.5 w-3.5 text-blue-500" />
              Tài khoản của tôi
            </Link>
          </DropdownMenuItem>
          <DropdownMenuItem
            className="flex items-center gap-2 rounded-lg px-2 py-1.5 text-xs text-foreground hover:bg-muted cursor-pointer"
            asChild
          >
            <Link href="/orders">
              <Package className="h-3.5 w-3.5 text-indigo-500" />
              Đơn hàng của tôi
            </Link>
          </DropdownMenuItem>

          {isAdmin && (
            <>
              <DropdownMenuSeparator className="my-1 h-px bg-border" />
              <DropdownMenuItem
                className="flex items-center gap-2 rounded-lg px-2 py-1.5 text-xs text-red-500 hover:bg-red-500/10 cursor-pointer font-medium"
                asChild
              >
                <Link href="/admin">
                  <ShieldAlert className="h-3.5 w-3.5" />
                  Trang Quản trị Admin
                </Link>
              </DropdownMenuItem>
            </>
          )}
          <DropdownMenuSeparator className="my-1 h-px bg-border" />
          <DropdownMenuItem
            onClick={onLogout}
            className="flex items-center gap-2 rounded-lg px-2 py-1.5 text-xs text-muted-foreground hover:bg-destructive/10 hover:text-destructive cursor-pointer"
          >
            <LogOut className="h-3.5 w-3.5" />
            Đăng xuất
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}

