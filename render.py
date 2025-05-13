import esper
from components import *
import pygame
import cProfile
import time
from typing import List, Tuple, Dict, Set

class QuadTree:
    def __init__(self, boundary: pygame.Rect, capacity: int = 10, max_depth: int = 5, depth: int = 0):
        self.boundary = boundary
        self.capacity = capacity
        self.max_depth = max_depth
        self.depth = depth
        self.entities: List[Tuple[int, Position, Renderable]] = []
        self.divided = False
        self.northwest = None
        self.northeast = None
        self.southwest = None
        self.southeast = None

    def point_in_bounds(self, x: float, y: float) -> bool:
        # Inclusive boundary check
        return (self.boundary.left <= x <= self.boundary.right and
                self.boundary.top <= y <= self.boundary.bottom)

    def subdivide(self):
        x = self.boundary.x
        y = self.boundary.y
        w = self.boundary.width // 2
        h = self.boundary.height // 2

        # Ensure boundaries overlap at the dividing lines
        nw = pygame.Rect(x, y, w + 1, h + 1)  # Include dividing lines
        ne = pygame.Rect(x + w, y, w + 1, h + 1)
        sw = pygame.Rect(x, y + h, w + 1, h + 1)
        se = pygame.Rect(x + w, y + h, w + 1, h + 1)

        self.northwest = QuadTree(nw, self.capacity, self.max_depth, self.depth + 1)
        self.northeast = QuadTree(ne, self.capacity, self.max_depth, self.depth + 1)
        self.southwest = QuadTree(sw, self.capacity, self.max_depth, self.depth + 1)
        self.southeast = QuadTree(se, self.capacity, self.max_depth, self.depth + 1)
        self.divided = True

        # Redistribute existing entities
        for entity in self.entities:
            self._insert_to_children(entity)
        self.entities.clear()

    def remove(self, entity_id: int) -> bool:
        # Remove from current level
        for i, (eid, _, _) in enumerate(self.entities):
            if eid == entity_id:
                self.entities.pop(i)
                return True

        # If divided, try to remove from children
        if self.divided:
            return (self.northwest.remove(entity_id) or
                    self.northeast.remove(entity_id) or
                    self.southwest.remove(entity_id) or
                    self.southeast.remove(entity_id))
        return False

    def _insert_to_children(self, entity):
        _, pos, _ = entity
        x, y = pos.x, pos.y
        
        # Try to insert into each quadrant that contains the point
        # This allows points on boundaries to exist in multiple quadrants
        inserted = False
        if self.northwest.point_in_bounds(x, y):
            self.northwest.insert(entity)
            inserted = True
        if self.northeast.point_in_bounds(x, y):
            self.northeast.insert(entity)
            inserted = True
        if self.southwest.point_in_bounds(x, y):
            self.southwest.insert(entity)
            inserted = True
        if self.southeast.point_in_bounds(x, y):
            self.southeast.insert(entity)
            inserted = True
        
        # If point wasn't inserted anywhere (shouldn't happen with overlapping bounds)
        if not inserted:
            # Fallback: insert into the quadrant it's closest to
            mid_x = self.boundary.centerx
            mid_y = self.boundary.centery
            if x <= mid_x:
                if y <= mid_y:
                    self.northwest.insert(entity)
                else:
                    self.southwest.insert(entity)
            else:
                if y <= mid_y:
                    self.northeast.insert(entity)
                else:
                    self.southeast.insert(entity)

    def insert(self, entity: Tuple[int, Position, Renderable]) -> bool:
        # Check if point is within boundary
        _, pos, _ = entity
        if not self.point_in_bounds(pos.x, pos.y):
            return False

        # If space available and at max depth, add here
        if len(self.entities) < self.capacity or self.depth >= self.max_depth:
            self.entities.append(entity)
            return True

        # Subdivide if needed
        if not self.divided:
            self.subdivide()

        # Try to insert into children
        return self._insert_to_children(entity)

    def query_range(self, range_rect: pygame.Rect) -> List[Tuple[int, Position, Renderable]]:
        found_entities = []

        # Use inclusive collision check
        if not (self.boundary.right < range_rect.left or
                self.boundary.left > range_rect.right or
                self.boundary.bottom < range_rect.top or
                self.boundary.top > range_rect.bottom):
            
            # Add entities at this level that are within range
            for entity in self.entities:
                _, pos, _ = entity
                if (range_rect.left <= pos.x <= range_rect.right and
                    range_rect.top <= pos.y <= range_rect.bottom):
                    found_entities.append(entity)

            # If subdivided, check children
            if self.divided:
                found_entities.extend(self.northwest.query_range(range_rect))
                found_entities.extend(self.northeast.query_range(range_rect))
                found_entities.extend(self.southwest.query_range(range_rect))
                found_entities.extend(self.southeast.query_range(range_rect))

        return found_entities

class RenderSystem(esper.Processor):
    def __init__(self, screen, camera, tile_size, background = None):
        super().__init__()
        self.screen = screen
        self.camera = camera
        self.tile_size = tile_size
        self.background = background
        self.enable_culling = (background is None)
        self.enable_quadtree = (background is None)
        self.profiler = cProfile.Profile()
        self.frame_times = []
        self.last_stats_time = time.time()
        self.frames_since_last_stats = 0
        # Initialize quadtree with a large enough boundary
        self.quadtree = None

    def is_visible(self, x, y):
        screen_x = x * self.camera.zoom + self.camera.offset_x
        screen_y = y * self.camera.zoom + self.camera.offset_y
        margin = self.tile_size
        return (-margin <= screen_x <= self.screen.get_width() + margin and
                -margin <= screen_y <= self.screen.get_height() + margin)

    def toggle_culling(self):
        self.enable_culling = not self.enable_culling
        print(f"Culling {'enabled' if self.enable_culling else 'disabled'}")
        self.reset_stats()

    def toggle_quadtree(self):
        self.enable_quadtree = not self.enable_quadtree
        print(f"Quadtree {'enabled' if self.enable_quadtree else 'disabled'}")
        self.reset_stats()
        if not self.enable_quadtree:
            self.quadtree = None

    def reset_stats(self):
        self.frame_times.clear()
        self.profiler = cProfile.Profile()
        self.frames_since_last_stats = 0
        self.last_stats_time = time.time()

    def print_stats(self):
        current_time = time.time()
        elapsed = current_time - self.last_stats_time
        if elapsed >= 5.0:
            avg_frame_time = sum(self.frame_times) / len(self.frame_times) if self.frame_times else 0
            fps = self.frames_since_last_stats / elapsed
            print(f"\nRendering Statistics:")
            print(f"Culling: {'enabled' if self.enable_culling else 'disabled'}")
            print(f"Quadtree: {'enabled' if self.enable_quadtree else 'disabled'}")
            print(f"Average frame time: {avg_frame_time*1000:.2f}ms")
            print(f"FPS: {fps:.1f}")
            print(f"Frames rendered: {self.frames_since_last_stats}")
            self.profiler.print_stats(sort='cumulative')
            self.reset_stats()

    def initialize_quadtree(self, entities):
        # Find the bounds of all entities
        if not entities:
            return
        
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')
        
        for _, (pos, _) in entities:
            min_x = min(min_x, pos.x)
            min_y = min(min_y, pos.y)
            max_x = max(max_x, pos.x)
            max_y = max(max_y, pos.y)
        
        # Add padding to the boundary
        padding = self.tile_size * 2
        boundary = pygame.Rect(
            min_x - padding,
            min_y - padding,
            max_x - min_x + padding * 2,
            max_y - min_y + padding * 2
        )
        
        # Create new quadtree
        self.quadtree = QuadTree(boundary)
        
        # Insert all entities and track their positions
        for entity, (pos, renderable) in entities:
            self.quadtree.insert((entity, pos, renderable))

    def update_entities(self, entities):
        for entity, (pos, renderable, _) in entities:
            self.quadtree.remove(entity)
            self.quadtree.insert((entity, pos, renderable))

    def process(self, dt):
        start_time = time.time()
        self.profiler.enable()

        if self.background:
            self.screen.blit(self.background, (0, 0))

        # Initialize or update quadtree
        if self.enable_quadtree:
            if self.quadtree is None:
                entities = list(esper.get_components(Position, Renderable))
                self.initialize_quadtree(entities)
            else:
                entities = list(esper.get_components(Position, Renderable, Moveable))
                self.update_entities(entities)

        rendered_count = 0
        total_count = 0
        
        # Calculate visible area in world coordinates
        left = (-self.camera.offset_x - self.tile_size) / self.camera.zoom
        right = (self.screen.get_width() - self.camera.offset_x + self.tile_size) / self.camera.zoom
        top = (-self.camera.offset_y - self.tile_size) / self.camera.zoom
        bottom = (self.screen.get_height() - self.camera.offset_y + self.tile_size) / self.camera.zoom
        visible_rect = pygame.Rect(left, top, right - left, bottom - top)

        # Get visible entities
        if self.enable_quadtree and self.quadtree:
            visible_entities = self.quadtree.query_range(visible_rect)
        else:
            entities = list(esper.get_components(Position, Renderable))
            visible_entities = [(entity, pos, renderable) for entity, (pos, renderable) in entities]

        visible_entities.sort(key=lambda ent: ent[2].z)

        # Render visible entities
        for _, position, renderable in visible_entities:
            if self.enable_culling and not self.is_visible(position.x, position.y):
                continue

            image = renderable.image
            if not image:
                continue

            # Calculate screen position for the center point
            center_x = position.x * self.camera.zoom + self.camera.offset_x
            center_y = position.y * self.camera.zoom + self.camera.offset_y - position.z
            
            # Offset by half the sprite dimensions to center the sprite at the position
            x = center_x - image.get_width() // 2
            y = center_y - image.get_height() // 2
            
            self.screen.blit(image, (x, y))
            rendered_count += 1

        self.profiler.disable()
        end_time = time.time()
        self.frame_times.append(end_time - start_time)
        self.frames_since_last_stats += 1
        
        #self.print_stats()

        #if total_count > 0:
        #    culling_status = "enabled" if self.enable_culling else "disabled"
        #    quadtree_status = "enabled" if self.enable_quadtree else "disabled"
        #    print(f"\rFrame: Rendered {rendered_count}/{total_count} entities ({(rendered_count/total_count)*100:.1f}%) - Culling {culling_status} - Quadtree {quadtree_status}", end="")
