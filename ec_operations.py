#!/usr/bin/env python3
"""
Elliptic Curve Operations for secp256k1
Implements point arithmetic and utilities for Bitcoin's elliptic curve
"""

import hashlib
from typing import Tuple, Optional

# secp256k1 parameters
P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
Gy = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8
G = (Gx, Gy)
A = 0
B = 7


class Point:
    """Represents a point on the secp256k1 elliptic curve"""
    
    def __init__(self, x: Optional[int] = None, y: Optional[int] = None):
        self.x = x
        self.y = y
        self.is_infinity = (x is None or y is None)
    
    def __eq__(self, other):
        if not isinstance(other, Point):
            return False
        if self.is_infinity and other.is_infinity:
            return True
        if self.is_infinity or other.is_infinity:
            return False
        return self.x == other.x and self.y == other.y
    
    def __str__(self):
        if self.is_infinity:
            return "Point(INF)"
        return f"Point({hex(self.x)}, {hex(self.y)})"
    
    def __repr__(self):
        return self.__str__()


def mod_inverse(a: int, m: int) -> int:
    """Compute modular inverse using extended Euclidean algorithm"""
    if a < 0:
        a = (a % m + m) % m
    
    def extended_gcd(a, b):
        if a == 0:
            return b, 0, 1
        gcd, x1, y1 = extended_gcd(b % a, a)
        x = y1 - (b // a) * x1
        y = x1
        return gcd, x, y
    
    gcd, x, _ = extended_gcd(a % m, m)
    if gcd != 1:
        raise ValueError("Modular inverse does not exist")
    return (x % m + m) % m


def point_add(p1: Point, p2: Point) -> Point:
    """Add two points on the elliptic curve"""
    if p1.is_infinity:
        return p2
    if p2.is_infinity:
        return p1
    
    if p1.x == p2.x:
        if p1.y == p2.y:
            # Point doubling
            s = (3 * p1.x * p1.x * mod_inverse(2 * p1.y, P)) % P
        else:
            # Points are inverses
            return Point()
    else:
        # Point addition
        s = ((p2.y - p1.y) * mod_inverse(p2.x - p1.x, P)) % P
    
    x3 = (s * s - p1.x - p2.x) % P
    y3 = (s * (p1.x - x3) - p1.y) % P
    
    return Point(x3, y3)


def point_double(p: Point) -> Point:
    """Double a point on the elliptic curve"""
    if p.is_infinity:
        return p
    
    if p.y == 0:
        return Point()
    
    s = (3 * p.x * p.x * mod_inverse(2 * p.y, P)) % P
    x3 = (s * s - 2 * p.x) % P
    y3 = (s * (p.x - x3) - p.y) % P
    
    return Point(x3, y3)


def point_multiply(k: int, point: Point = None) -> Point:
    """Multiply a point by a scalar using double-and-add algorithm"""
    if point is None:
        point = Point(Gx, Gy)
    
    if k == 0:
        return Point()
    
    if k < 0:
        k = -k
        point = Point(point.x, (-point.y) % P)
    
    result = Point()
    addend = point
    
    while k:
        if k & 1:
            result = point_add(result, addend)
        addend = point_double(addend)
        k >>= 1
    
    return result


def point_subtract(p1: Point, p2: Point) -> Point:
    """Subtract p2 from p1"""
    if p2.is_infinity:
        return p1
    p2_neg = Point(p2.x, (-p2.y) % P)
    return point_add(p1, p2_neg)


def compress_point(point: Point) -> bytes:
    """Compress point to 33 bytes (02/03 prefix + x coordinate)"""
    if point.is_infinity:
        return b'\x00' * 33
    prefix = b'\x02' if point.y % 2 == 0 else b'\x03'
    return prefix + point.x.to_bytes(32, 'big')


def decompress_point(compressed: bytes) -> Point:
    """Decompress point from 33 bytes"""
    if len(compressed) != 33:
        raise ValueError("Invalid compressed point length")
    
    if compressed[0] not in [0x02, 0x03]:
        raise ValueError("Invalid compression prefix")
    
    x = int.from_bytes(compressed[1:], 'big')
    
    # Calculate y^2 = x^3 + 7 (mod p)
    y_squared = (pow(x, 3, P) + B) % P
    
    # Calculate y using modular square root
    y = pow(y_squared, (P + 1) // 4, P)
    
    # Choose correct y based on prefix
    if (y % 2 == 0) != (compressed[0] == 0x02):
        y = P - y
    
    return Point(x, y)


def hash_point(point: Point) -> int:
    """Hash a point to an integer"""
    if point.is_infinity:
        return 0
    data = point.x.to_bytes(32, 'big') + point.y.to_bytes(32, 'big')
    return int.from_bytes(hashlib.sha256(data).digest(), 'big')


def public_key_to_point(pubkey: str) -> Point:
    """Convert public key hex string to Point"""
    pubkey = pubkey.strip()
    
    if len(pubkey) == 66:  # Compressed (02/03 + 64 hex chars)
        compressed = bytes.fromhex(pubkey)
        return decompress_point(compressed)
    elif len(pubkey) == 130:  # Uncompressed (04 + 128 hex chars)
        if pubkey[:2] != '04':
            raise ValueError("Invalid uncompressed public key prefix")
        x = int(pubkey[2:66], 16)
        y = int(pubkey[66:130], 16)
        return Point(x, y)
    else:
        raise ValueError("Invalid public key format")


def point_to_public_key(point: Point, compressed: bool = True) -> str:
    """Convert Point to public key hex string"""
    if point.is_infinity:
        return ""
    
    if compressed:
        return compress_point(point).hex()
    else:
        prefix = '04'
        x_hex = point.x.to_bytes(32, 'big').hex()
        y_hex = point.y.to_bytes(32, 'big').hex()
        return prefix + x_hex + y_hex
