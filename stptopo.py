# Brennan Hall - 861198641
# CS164 Final Project - Topology

from mininet.topo import Topo

class STPTopo( Topo ):
	def __init__( self ):
		Topo.__init__( self )
		h1 = self.addHost( 'b1', ip = '10.0.0.1/24' )
		h2 = self.addHost( 'b2', ip = '10.0.0.2/24' )
		h3 = self.addHost( 'b3', ip = '10.0.0.3/24' )
		h4 = self.addHost( 'b4', ip = '10.0.0.4/24' )
		switch = self.addSwitch( 's1' )
		self.addLink( h1, switch )
		self.addLink( h2, switch )
		self.addLink( h3, switch )
		self.addLink( h4, switch )

topos = { 'stptopo': ( lambda: STPTopo() ) }


